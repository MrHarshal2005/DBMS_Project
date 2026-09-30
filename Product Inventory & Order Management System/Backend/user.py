from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from extensions import db


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False, index=True)
    phone = db.Column(db.String(20), nullable=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(10), nullable=False)  # SELLER or BUYER
    status = db.Column(db.String(20), nullable=False, default="ACTIVE")  # ACTIVE / INACTIVE
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    products = db.relationship("Product", backref="seller", lazy="dynamic",
                                foreign_keys="Product.seller_id")
    buyer_orders = db.relationship("Order", backref="buyer", lazy="dynamic",
                                    foreign_keys="Order.buyer_id")

    def set_password(self, raw_password):
        self.password_hash = generate_password_hash(raw_password)

    def check_password(self, raw_password):
        return check_password_hash(self.password_hash, raw_password)

    def is_seller(self):
        return self.role == "SELLER"

    def is_buyer(self):
        return self.role == "BUYER"

    def __repr__(self):
        return f"<User {self.email} ({self.role})>"
