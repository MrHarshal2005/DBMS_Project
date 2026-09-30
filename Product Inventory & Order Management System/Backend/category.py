from datetime import datetime
from extensions import db


class Category(db.Model):
    __tablename__ = "categories"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False, index=True)
    description = db.Column(db.String(255), nullable=True)
    status = db.Column(db.String(20), nullable=False, default="ACTIVE")  # ACTIVE / INACTIVE
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    products = db.relationship("Product", backref="category", lazy="dynamic")

    def __repr__(self):
        return f"<Category {self.name}>"
