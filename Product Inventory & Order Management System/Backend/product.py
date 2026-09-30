from datetime import datetime
from extensions import db


class Product(db.Model):
    __tablename__ = "products"

    id = db.Column(db.Integer, primary_key=True)
    seller_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    category_id = db.Column(db.Integer, db.ForeignKey("categories.id"), nullable=False, index=True)
    name = db.Column(db.String(150), nullable=False)
    sku = db.Column(db.String(64), unique=True, nullable=False, index=True)
    description = db.Column(db.Text, nullable=True)
    image = db.Column(db.String(255), nullable=True)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    stock_quantity = db.Column(db.Integer, nullable=False, default=0)
    minimum_stock = db.Column(db.Integer, nullable=False, default=5)
    status = db.Column(db.String(20), nullable=False, default="ACTIVE")  # ACTIVE / INACTIVE
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    inventory_transactions = db.relationship("InventoryTransaction", backref="product",
                                              lazy="dynamic")

    @property
    def is_low_stock(self):
        return self.stock_quantity <= self.minimum_stock

    @property
    def is_available(self):
        return self.status == "ACTIVE" and self.stock_quantity > 0

    @property
    def image_url(self):
        if self.image:
            return f"/static/uploads/{self.image}"
        return "/static/images/placeholder.png"

    def __repr__(self):
        return f"<Product {self.sku} - {self.name}>"
