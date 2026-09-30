from flask import Flask, render_template, redirect, url_for
from flask_login import current_user

from config import Config
from extensions import db, login_manager, csrf


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)

    # --- models must be imported after db.init_app so they register on it
    from models import User  # noqa: F401

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # --- blueprints
    from routes.auth import auth_bp
    from routes.buyer import buyer_bp
    from routes.seller import seller_bp
    from routes.products import products_bp
    from routes.cart import cart_bp
    from routes.orders import orders_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(buyer_bp)
    app.register_blueprint(seller_bp)
    app.register_blueprint(products_bp)
    app.register_blueprint(cart_bp)
    app.register_blueprint(orders_bp)

    # --- home route
    @app.route("/")
    def index():
        if current_user.is_authenticated:
            if current_user.is_seller():
                return redirect(url_for("seller.dashboard"))
            return redirect(url_for("buyer.dashboard"))
        return redirect(url_for("products.catalog"))

    # --- template helpers
    from utils.helpers import format_currency

    @app.template_filter("currency")
    def currency_filter(amount):
        return format_currency(amount)

    @app.context_processor
    def inject_cart_count():
        count = 0
        if current_user.is_authenticated and current_user.is_buyer():
            from models.cart import Cart
            cart = Cart.query.filter_by(buyer_id=current_user.id).first()
            count = cart.item_count if cart else 0
        return {"cart_item_count": count}

    # --- error handlers
    @app.errorhandler(403)
    def forbidden(e):
        return render_template("errors/403.html"), 403

    @app.errorhandler(404)
    def not_found(e):
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def server_error(e):
        db.session.rollback()
        return render_template("errors/500.html"), 500

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
