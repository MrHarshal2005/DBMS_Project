from collections import defaultdict

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user

from extensions import db
from models.cart import Cart, CartItem
from models.order import Order, OrderItem
from utils.auth import buyer_required
from utils.validators import is_valid_email, is_valid_phone, is_valid_pincode, clean_str
from utils.helpers import generate_order_number
from utils.inventory_service import deduct_for_sale, restore_for_cancellation, InsufficientStockError

orders_bp = Blueprint("orders", __name__)


@orders_bp.route("/checkout", methods=["GET", "POST"])
@login_required
@buyer_required
def checkout():
    cart = Cart.query.filter_by(buyer_id=current_user.id).first()
    items = cart.items.all() if cart else []

    if not items:
        flash("Your cart is empty.", "warning")
        return redirect(url_for("products.catalog"))

    # Validate stock up front so the buyer sees a clear error before submitting.
    for item in items:
        if item.quantity > item.product.stock_quantity:
            flash(
                f"Only {item.product.stock_quantity} units of "
                f"'{item.product.name}' are available.", "danger"
            )
            return redirect(url_for("cart.view_cart"))

    if request.method == "POST":
        name = clean_str(request.form.get("delivery_name"), 120)
        phone = clean_str(request.form.get("delivery_phone"), 20)
        email = clean_str(request.form.get("delivery_email"), 150)
        address = clean_str(request.form.get("delivery_address"), 255)
        city = clean_str(request.form.get("delivery_city"), 100)
        state = clean_str(request.form.get("delivery_state"), 100)
        pincode = clean_str(request.form.get("delivery_pincode"), 15)

        errors = []
        if not name:
            errors.append("Delivery name is required.")
        if not is_valid_phone(phone):
            errors.append("Please enter a valid phone number.")
        if not is_valid_email(email):
            errors.append("Please enter a valid email address.")
        if not address:
            errors.append("Delivery address is required.")
        if not city:
            errors.append("City is required.")
        if not state:
            errors.append("State is required.")
        if not is_valid_pincode(pincode):
            errors.append("Please enter a valid pincode.")

        if errors:
            for e in errors:
                flash(e, "danger")
            return render_template("orders/checkout.html", items=items, cart=cart,
                                    form=request.form)

        # Re-fetch items fresh and lock in one DB transaction to keep
        # stock deduction + order creation atomic and race-safe.
        try:
            items_by_seller = defaultdict(list)
            for item in items:
                items_by_seller[item.product.seller_id].append(item)

            created_orders = []

            for seller_id, seller_items in items_by_seller.items():
                order_number = generate_order_number()
                order_total = 0

                order = Order(
                    order_number=order_number,
                    buyer_id=current_user.id,
                    seller_id=seller_id,
                    payment_method="COD",
                    payment_status="PENDING",
                    order_status="Pending",
                    delivery_name=name,
                    delivery_phone=phone,
                    delivery_email=email,
                    delivery_address=address,
                    delivery_city=city,
                    delivery_state=state,
                    delivery_pincode=pincode,
                    total_amount=0,
                )
                db.session.add(order)
                db.session.flush()  # get order.id

                for item in seller_items:
                    product = item.product
                    # Server-side price/stock re-check -- never trust the client.
                    unit_price = product.price
                    quantity = item.quantity

                    deduct_for_sale(product, quantity, order_number)

                    subtotal = unit_price * quantity
                    order_total += subtotal

                    order_item = OrderItem(
                        order_id=order.id,
                        product_id=product.id,
                        product_name=product.name,
                        quantity=quantity,
                        unit_price=unit_price,
                        subtotal=subtotal,
                    )
                    db.session.add(order_item)

                order.total_amount = order_total
                created_orders.append(order)

            # Clear the cart now that everything succeeded.
            CartItem.query.filter_by(cart_id=cart.id).delete()

            db.session.commit()

        except InsufficientStockError as e:
            db.session.rollback()
            flash(str(e), "danger")
            return redirect(url_for("cart.view_cart"))
        except Exception:
            db.session.rollback()
            flash("Something went wrong while placing your order. Please try again.", "danger")
            return redirect(url_for("cart.view_cart"))

        flash("Order placed successfully.", "success")
        if len(created_orders) == 1:
            return redirect(url_for("orders.buyer_order_detail", order_id=created_orders[0].id))
        return redirect(url_for("orders.buyer_orders"))

    grand_total = sum(item.subtotal for item in items)
    return render_template("orders/checkout.html", items=items, cart=cart,
                            grand_total=grand_total, form={})


@orders_bp.route("/orders")
@login_required
@buyer_required
def buyer_orders():
    page = request.args.get("page", 1, type=int)
    pagination = (Order.query.filter_by(buyer_id=current_user.id)
                  .order_by(Order.created_at.desc())
                  .paginate(page=page, per_page=15, error_out=False))
    return render_template("orders/buyer_orders.html", pagination=pagination,
                            orders=pagination.items)


@orders_bp.route("/order/<int:order_id>")
@login_required
@buyer_required
def buyer_order_detail(order_id):
    order = Order.query.filter_by(id=order_id, buyer_id=current_user.id).first_or_404()
    return render_template("orders/buyer_order_detail.html", order=order)


@orders_bp.route("/order/<int:order_id>/cancel", methods=["POST"])
@login_required
@buyer_required
def cancel_order(order_id):
    order = Order.query.filter_by(id=order_id, buyer_id=current_user.id).first_or_404()

    if not order.can_cancel():
        flash("This order can no longer be cancelled.", "danger")
        return redirect(url_for("orders.buyer_order_detail", order_id=order.id))

    try:
        for item in order.items:
            if item.product:
                restore_for_cancellation(item.product, item.quantity, order.order_number)
        order.order_status = "Cancelled"
        db.session.commit()
        flash("Order cancelled and stock restored.", "success")
    except Exception:
        db.session.rollback()
        flash("Could not cancel the order. Please try again.", "danger")

    return redirect(url_for("orders.buyer_order_detail", order_id=order.id))
