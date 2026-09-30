from datetime import datetime
from extensions import db


class InventoryTransaction(db.Model):
    __tablename__ = "inventory_transactions"

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False, index=True)
    seller_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    transaction_type = db.Column(db.String(20), nullable=False)
    # PURCHASE, SALE, RETURN, ADJUSTMENT, CANCELLATION
    quantity_change = db.Column(db.Integer, nullable=False)  # positive or negative
    previous_stock = db.Column(db.Integer, nullable=False)
    new_stock = db.Column(db.Integer, nullable=False)
    reference_id = db.Column(db.String(50), nullable=True)  # e.g. order_number
    notes = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    def __repr__(self):
        return f"<InventoryTxn {self.transaction_type} {self.quantity_change} product={self.product_id}>"
