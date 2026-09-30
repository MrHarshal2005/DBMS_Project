from datetime import datetime
from extensions import db


class Order(db.Model):
    __tablename__ = "orders"

    id = db.Column(db.Integer, primary_key=True)
    order_number = db.Column(db.String(30), unique=True, nullable=False, index=True)
    buyer_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    seller_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)

    total_amount = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    payment_method = db.Column(db.String(30), nullable=False, default="COD")
    payment_status = db.Column(db.String(20), nullable=False, default="PENDING")  # PENDING/PAID
    order_status = db.Column(db.String(20), nullable=False, default="Pending", index=True)

    delivery_name = db.Column(db.String(120), nullable=False)
    delivery_phone = db.Column(db.String(20), nullable=False)
    delivery_email = db.Column(db.String(150), nullable=False)
    delivery_address = db.Column(db.String(255), nullable=False)
    delivery_city = db.Column(db.String(100), nullable=False)
    delivery_state = db.Column(db.String(100), nullable=False)
    delivery_pincode = db.Column(db.String(15), nullable=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    seller = db.relationship("User", foreign_keys=[seller_id])
    items = db.relationship("OrderItem", backref="order", lazy="dynamic",
                             cascade="all, delete-orphan")

    STATUS_FLOW = ["Pending", "Confirmed", "Packed", "Shipped", "Delivered"]
    CANCELLABLE_STATUSES = {"Pending", "Confirmed", "Packed"}

    def can_cancel(self):
        return self.order_status in self.CANCELLABLE_STATUSES

    def can_transition_to(self, new_status):
        """Only allow moving forward one step in the flow, or cancelling."""
        if new_status == "Cancelled":
            return self.can_cancel()
        if self.order_status not in self.STATUS_FLOW:
            return False
        if new_status not in self.STATUS_FLOW:
            return False
        current_idx = self.STATUS_FLOW.index(self.order_status)
        new_idx = self.STATUS_FLOW.index(new_status)
        return new_idx == current_idx + 1

    def __repr__(self):
        return f"<Order {self.order_number} - {self.order_status}>"


class OrderItem(db.Model):
    __tablename__ = "order_items"

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey("orders.id"), nullable=False, index=True)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=True)
    product_name = db.Column(db.String(150), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Numeric(10, 2), nullable=False)
    subtotal = db.Column(db.Numeric(10, 2), nullable=False)

    product = db.relationship("Product")
