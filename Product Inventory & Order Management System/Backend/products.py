from flask import Blueprint, render_template, request, abort
from flask_login import login_required

from models.product import Product
from models.category import Category

products_bp = Blueprint("products", __name__)


@products_bp.route("/products")
def catalog():
    page = request.args.get("page", 1, type=int)
    q = request.args.get("q", "", type=str).strip()
    category_id = request.args.get("category", type=int)
    sort = request.args.get("sort", "newest")

    query = Product.query.filter_by(status="ACTIVE")

    if q:
        like = f"%{q}%"
        query = query.filter(Product.name.ilike(like))

    if category_id:
        query = query.filter_by(category_id=category_id)

    if sort == "price_low":
        query = query.order_by(Product.price.asc())
    elif sort == "price_high":
        query = query.order_by(Product.price.desc())
    elif sort == "name":
        query = query.order_by(Product.name.asc())
    else:
        query = query.order_by(Product.created_at.desc())

    pagination = query.paginate(page=page, per_page=12, error_out=False)
    categories = Category.query.filter_by(status="ACTIVE").order_by(Category.name).all()

    return render_template(
        "buyer/catalog.html",
        products=pagination.items,
        pagination=pagination,
        categories=categories,
        q=q,
        category_id=category_id,
        sort=sort,
    )


@products_bp.route("/product/<int:product_id>")
def detail(product_id):
    product = Product.query.get_or_404(product_id)
    if product.status != "ACTIVE":
        abort(404)
    related = (Product.query
               .filter(Product.category_id == product.category_id,
                       Product.id != product.id,
                       Product.status == "ACTIVE")
               .limit(4).all())
    return render_template("buyer/product_detail.html", product=product, related=related)
