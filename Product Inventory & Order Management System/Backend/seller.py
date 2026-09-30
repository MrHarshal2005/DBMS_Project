from datetime import datetime, timedelta

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from sqlalchemy import func

from extensions import db
from models.product import Product
from models.category import Category
from models.order import Order, OrderItem
from models.inventory import InventoryTransaction
from utils.auth import seller_required
from utils.validators import (parse_positive_decimal, parse_non_negative_int,
                               clean_str)
from utils.helpers import save_product_image, delete_product_image
from utils.inventory_service import add_purchase_stock, manual_adjustment

seller_bp = Blueprint("seller", __name__)


# ---------------------------------------------------------------- dashboard
@seller_bp.route("/seller/dashboard")
@login_required
@seller_required
def dashboard():
    seller_id = current_user.id

    total_products = Product.query.filter_by(seller_id=seller_id).count()
    total_stock = (db.session.query(func.coalesce(func.sum(Product.stock_quantity), 0))
                    .filter_by(seller_id=seller_id).scalar())
    total_orders = Order.query.filter_by(seller_id=seller_id).count()
    pending_orders = Order.query.filter_by(seller_id=seller_id).filter(
        Order.order_status.in_(["Pending", "Confirmed", "Packed", "Shipped"])).count()
    completed_orders = Order.query.filter_by(seller_id=seller_id,
                                              order_status="Delivered").count()
    total_sales = (db.session.query(func.coalesce(func.sum(Order.total_amount), 0))
                    .filter_by(seller_id=seller_id)
                    .filter(Order.order_status != "Cancelled").scalar())
    low_stock_products = Product.query.filter(
        Product.seller_id == seller_id,
        Product.stock_quantity <= Product.minimum_stock,
        Product.status == "ACTIVE",
    ).all()

    recent_orders = (Order.query.filter_by(seller_id=seller_id)
                      .order_by(Order.created_at.desc()).limit(5).all())

    return render_template(
        "seller/dashboard.html",
        total_products=total_products,
        total_stock=total_stock,
        total_orders=total_orders,
        pending_orders=pending_orders,
        completed_orders=completed_orders,
        total_sales=total_sales,
        low_stock_products=low_stock_products,
        recent_orders=recent_orders,
    )


# ----------------------------------------------------------------- products
@seller_bp.route("/seller/products")
@login_required
@seller_required
def products():
    page = request.args.get("page", 1, type=int)
    q = request.args.get("q", "", type=str).strip()

    query = Product.query.filter_by(seller_id=current_user.id)
    if q:
        query = query.filter(Product.name.ilike(f"%{q}%"))

    pagination = query.order_by(Product.created_at.desc()).paginate(
        page=page, per_page=12, error_out=False)

    return render_template("seller/products.html", pagination=pagination,
                            products=pagination.items, q=q)


def _product_form_context(product=None):
    categories = Category.query.filter_by(status="ACTIVE").order_by(Category.name).all()
    return {"categories": categories, "product": product}


@seller_bp.route("/seller/products/add", methods=["GET", "POST"])
@login_required
@seller_required
def add_product():
    if request.method == "POST":
        return _save_product(product=None)
    return render_template("seller/product_form.html", **_product_form_context())


@seller_bp.route("/seller/products/edit/<int:product_id>", methods=["GET", "POST"])
@login_required
@seller_required
def edit_product(product_id):
    product = Product.query.filter_by(id=product_id, seller_id=current_user.id).first_or_404()
    if request.method == "POST":
        return _save_product(product=product)
    return render_template("seller/product_form.html", **_product_form_context(product))


def _save_product(product):
    name = clean_str(request.form.get("name"), 150)
    sku = clean_str(request.form.get("sku"), 64)
    category_id = request.form.get("category_id", type=int)
    description = clean_str(request.form.get("description"), 2000)
    price = parse_positive_decimal(request.form.get("price"), allow_zero=False)
    stock = parse_non_negative_int(request.form.get("stock_quantity"))
    min_stock = parse_non_negative_int(request.form.get("minimum_stock"))
    status = "ACTIVE" if request.form.get("status") == "ACTIVE" else "INACTIVE"
    image_file = request.files.get("image")

    errors = []
    if not name:
        errors.append("Product name is required.")
    if not sku:
        errors.append("SKU is required.")
    if not category_id or not Category.query.get(category_id):
        errors.append("A valid category is required.")
    if price is None:
        errors.append("Price must be a positive number.")
    if stock is None:
        errors.append("Stock cannot be negative.")
    if min_stock is None:
        errors.append("Minimum stock level cannot be negative.")

    existing_sku = Product.query.filter(Product.sku == sku).first()
    if existing_sku and (not product or existing_sku.id != product.id):
        errors.append("SKU must be unique. This SKU is already in use.")

    if errors:
        for e in errors:
            flash(e, "danger")
        return render_template("seller/product_form.html",
                                **_product_form_context(product))

    try:
        saved_image_name = save_product_image(image_file) if image_file else None
    except ValueError as e:
        flash(str(e), "danger")
        return render_template("seller/product_form.html",
                                **_product_form_context(product))

    if product is None:
        # stock_quantity starts at 0 here; add_purchase_stock below brings it
        # up to the requested amount and records the matching PURCHASE
        # transaction, so stock is never double-counted.
        product = Product(
            seller_id=current_user.id,
            name=name, sku=sku, category_id=category_id, description=description,
            price=price, stock_quantity=0, minimum_stock=min_stock, status=status,
        )
        if saved_image_name:
            product.image = saved_image_name
        db.session.add(product)
        db.session.flush()
        if stock:
            add_purchase_stock(product, stock, notes="Initial stock on product creation")
        db.session.commit()
        flash("Product added successfully.", "success")
    else:
        stock_diff = stock - product.stock_quantity
        product.name = name
        product.sku = sku
        product.category_id = category_id
        product.description = description
        product.price = price
        product.minimum_stock = min_stock
        product.status = status
        if saved_image_name:
            delete_product_image(product.image)
            product.image = saved_image_name
        if stock_diff != 0:
            manual_adjustment(product, stock_diff,
                               notes="Stock corrected via product edit")
        db.session.commit()
        flash("Product updated successfully.", "success")

    return redirect(url_for("seller.products"))


@seller_bp.route("/seller/products/toggle/<int:product_id>", methods=["POST"])
@login_required
@seller_required
def toggle_product(product_id):
    product = Product.query.filter_by(id=product_id, seller_id=current_user.id).first_or_404()
    product.status = "INACTIVE" if product.status == "ACTIVE" else "ACTIVE"
    db.session.commit()
    flash(f"Product {'activated' if product.status == 'ACTIVE' else 'deactivated'} successfully.",
          "success")
    return redirect(url_for("seller.products"))


# ---------------------------------------------------------------- inventory
@seller_bp.route("/seller/inventory")
@login_required
@seller_required
def inventory():
    products = Product.query.filter_by(seller_id=current_user.id).order_by(
        Product.stock_quantity.asc()).all()
    recent_transactions = (InventoryTransaction.query
                            .filter_by(seller_id=current_user.id)
                            .order_by(InventoryTransaction.created_at.desc())
                            .limit(30).all())
    return render_template("seller/inventory.html", products=products,
                            recent_transactions=recent_transactions)


@seller_bp.route("/seller/inventory/adjust/<int:product_id>", methods=["POST"])
@login_required
@seller_required
def adjust_inventory(product_id):
    product = Product.query.filter_by(id=product_id, seller_id=current_user.id).first_or_404()
    change = request.form.get("quantity_change", type=int)
    notes = clean_str(request.form.get("notes"), 255)

    if change is None or change == 0:
        flash("Please enter a non-zero quantity change.", "danger")
        return redirect(url_for("seller.inventory"))

    try:
        manual_adjustment(product, change, notes=notes or "Manual adjustment")
        db.session.commit()
        flash("Inventory adjusted successfully.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Could not adjust inventory: {e}", "danger")

    return redirect(url_for("seller.inventory"))


# ---------------------------------------------------------------- categories
@seller_bp.route("/seller/categories", methods=["GET", "POST"])
@login_required
@seller_required
def categories():
    if request.method == "POST":
        name = clean_str(request.form.get("name"), 100)
        description = clean_str(request.form.get("description"), 255)

        if not name:
            flash("Category name is required.", "danger")
        elif Category.query.filter_by(name=name).first():
            flash("A category with this name already exists.", "danger")
        else:
            db.session.add(Category(name=name, description=description, status="ACTIVE"))
            db.session.commit()
            flash("Category added successfully.", "success")
        return redirect(url_for("seller.categories"))

    all_categories = Category.query.order_by(Category.name).all()
    return render_template("seller/categories.html", categories=all_categories)


@seller_bp.route("/seller/categories/edit/<int:category_id>", methods=["POST"])
@login_required
@seller_required
def edit_category(category_id):
    category = Category.query.get_or_404(category_id)
    name = clean_str(request.form.get("name"), 100)
    description = clean_str(request.form.get("description"), 255)

    duplicate = Category.query.filter(Category.name == name,
                                       Category.id != category_id).first()
    if not name:
        flash("Category name is required.", "danger")
    elif duplicate:
        flash("A category with this name already exists.", "danger")
    else:
        category.name = name
        category.description = description
        db.session.commit()
        flash("Category updated successfully.", "success")
    return redirect(url_for("seller.categories"))


@seller_bp.route("/seller/categories/toggle/<int:category_id>", methods=["POST"])
@login_required
@seller_required
def toggle_category(category_id):
    category = Category.query.get_or_404(category_id)
    # Never hard-delete a category that has products; just toggle its status.
    category.status = "INACTIVE" if category.status == "ACTIVE" else "ACTIVE"
    db.session.commit()
    flash("Category status updated.", "success")
    return redirect(url_for("seller.categories"))


# -------------------------------------------------------------------- orders
@seller_bp.route("/seller/orders")
@login_required
@seller_required
def seller_orders():
    page = request.args.get("page", 1, type=int)
    status_filter = request.args.get("status", "")

    query = Order.query.filter_by(seller_id=current_user.id)
    if status_filter:
        query = query.filter_by(order_status=status_filter)

    pagination = query.order_by(Order.created_at.desc()).paginate(
        page=page, per_page=15, error_out=False)

    return render_template("seller/orders.html", pagination=pagination,
                            orders=pagination.items, status_filter=status_filter,
                            statuses=Order.STATUS_FLOW + ["Cancelled"])


@seller_bp.route("/seller/order/<int:order_id>")
@login_required
@seller_required
def seller_order_detail(order_id):
    order = Order.query.filter_by(id=order_id, seller_id=current_user.id).first_or_404()
    next_status = None
    if order.order_status in Order.STATUS_FLOW:
        idx = Order.STATUS_FLOW.index(order.order_status)
        if idx + 1 < len(Order.STATUS_FLOW):
            next_status = Order.STATUS_FLOW[idx + 1]
    return render_template("seller/order_detail.html", order=order, next_status=next_status)


@seller_bp.route("/seller/order/<int:order_id>/status", methods=["POST"])
@login_required
@seller_required
def update_order_status(order_id):
    order = Order.query.filter_by(id=order_id, seller_id=current_user.id).first_or_404()
    new_status = request.form.get("new_status")

    if not order.can_transition_to(new_status):
        flash(f"Cannot change order status from {order.order_status} to {new_status}.",
              "danger")
        return redirect(url_for("seller.seller_order_detail", order_id=order.id))

    from utils.inventory_service import restore_for_cancellation
    if new_status == "Cancelled":
        for item in order.items:
            if item.product:
                restore_for_cancellation(item.product, item.quantity, order.order_number)

    order.order_status = new_status
    db.session.commit()
    flash(f"Order status updated to {new_status}.", "success")
    return redirect(url_for("seller.seller_order_detail", order_id=order.id))


# ------------------------------------------------------------------- reports
@seller_bp.route("/seller/reports")
@login_required
@seller_required
def reports():
    seller_id = current_user.id
    range_key = request.args.get("range", "30")

    end_date = datetime.utcnow()
    if range_key == "today":
        start_date = end_date.replace(hour=0, minute=0, second=0, microsecond=0)
    elif range_key == "7":
        start_date = end_date - timedelta(days=7)
    elif range_key == "custom":
        try:
            start_date = datetime.strptime(request.args.get("start", ""), "%Y-%m-%d")
            end_date = datetime.strptime(request.args.get("end", ""), "%Y-%m-%d") + timedelta(days=1)
        except ValueError:
            start_date = end_date - timedelta(days=30)
    else:
        start_date = end_date - timedelta(days=30)

    base_query = Order.query.filter(
        Order.seller_id == seller_id,
        Order.created_at >= start_date,
        Order.created_at <= end_date,
    )

    total_sales = (db.session.query(func.coalesce(func.sum(Order.total_amount), 0))
                    .filter(Order.seller_id == seller_id, Order.created_at >= start_date,
                            Order.created_at <= end_date,
                            Order.order_status != "Cancelled").scalar())
    total_orders = base_query.count()
    completed_orders = base_query.filter(Order.order_status == "Delivered").count()
    cancelled_orders = base_query.filter(Order.order_status == "Cancelled").count()

    best_sellers = (db.session.query(
        OrderItem.product_name,
        func.sum(OrderItem.quantity).label("total_qty"),
        func.sum(OrderItem.subtotal).label("total_revenue"))
        .join(Order, Order.id == OrderItem.order_id)
        .filter(Order.seller_id == seller_id, Order.created_at >= start_date,
                Order.created_at <= end_date, Order.order_status != "Cancelled")
        .group_by(OrderItem.product_name)
        .order_by(func.sum(OrderItem.quantity).desc())
        .limit(5).all())

    low_stock_products = Product.query.filter(
        Product.seller_id == seller_id,
        Product.stock_quantity <= Product.minimum_stock,
    ).all()

    return render_template(
        "seller/reports.html",
        total_sales=total_sales,
        total_orders=total_orders,
        completed_orders=completed_orders,
        cancelled_orders=cancelled_orders,
        best_sellers=best_sellers,
        low_stock_products=low_stock_products,
        range_key=range_key,
    )
