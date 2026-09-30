from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user

from extensions import db
from models.product import Product
from models.cart import Cart, CartItem
from utils.auth import buyer_required

cart_bp = Blueprint("cart", __name__)


def _get_or_create_cart():
    cart = Cart.query.filter_by(buyer_id=current_user.id).first()
    if not cart:
        cart = Cart(buyer_id=current_user.id)
        db.session.add(cart)
        db.session.commit()
    return cart


@cart_bp.route("/cart")
@login_required
@buyer_required
def view_cart():
    cart = _get_or_create_cart()
    items = cart.items.order_by(CartItem.created_at.asc()).all()
    return render_template("cart/cart.html", cart=cart, items=items)


@cart_bp.route("/cart/add/<int:product_id>", methods=["POST"])
@login_required
@buyer_required
def add_to_cart(product_id):
    product = Product.query.get_or_404(product_id)

    if product.status != "ACTIVE":
        flash("This product is currently unavailable.", "danger")
        return redirect(url_for("products.detail", product_id=product_id))

    try:
        quantity = int(request.form.get("quantity", 1))
    except (TypeError, ValueError):
        quantity = 1
    quantity = max(1, quantity)

    cart = _get_or_create_cart()
    item = CartItem.query.filter_by(cart_id=cart.id, product_id=product.id).first()
    existing_qty = item.quantity if item else 0
    desired_qty = existing_qty + quantity

    if desired_qty > product.stock_quantity:
        flash(f"Only {product.stock_quantity} units are available.", "warning")
        desired_qty = product.stock_quantity
        if desired_qty <= 0:
            return redirect(url_for("products.detail", product_id=product_id))

    if item:
        item.quantity = desired_qty
    else:
        item = CartItem(cart_id=cart.id, product_id=product.id, quantity=desired_qty)
        db.session.add(item)

    db.session.commit()
    flash("Product added to cart.", "success")
    return redirect(request.referrer or url_for("cart.view_cart"))


@cart_bp.route("/cart/update/<int:item_id>", methods=["POST"])
@login_required
@buyer_required
def update_item(item_id):
    cart = _get_or_create_cart()
    item = CartItem.query.filter_by(id=item_id, cart_id=cart.id).first_or_404()

    try:
        quantity = int(request.form.get("quantity", 1))
    except (TypeError, ValueError):
        quantity = item.quantity

    if quantity <= 0:
        db.session.delete(item)
        db.session.commit()
        flash("Item removed from cart.", "info")
        return redirect(url_for("cart.view_cart"))

    if quantity > item.product.stock_quantity:
        flash(f"Only {item.product.stock_quantity} units are available.", "warning")
        quantity = item.product.stock_quantity

    item.quantity = quantity
    db.session.commit()
    return redirect(url_for("cart.view_cart"))


@cart_bp.route("/cart/remove/<int:item_id>", methods=["POST"])
@login_required
@buyer_required
def remove_item(item_id):
    cart = _get_or_create_cart()
    item = CartItem.query.filter_by(id=item_id, cart_id=cart.id).first_or_404()
    db.session.delete(item)
    db.session.commit()
    flash("Item removed from cart.", "info")
    return redirect(url_for("cart.view_cart"))


@cart_bp.route("/cart/clear", methods=["POST"])
@login_required
@buyer_required
def clear_cart():
    cart = _get_or_create_cart()
    CartItem.query.filter_by(cart_id=cart.id).delete()
    db.session.commit()
    flash("Cart cleared.", "info")
    return redirect(url_for("cart.view_cart"))
