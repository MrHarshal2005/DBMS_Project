"""
Centralised inventory mutation logic.

Every function here assumes it is being called inside an active
SQLAlchemy session/transaction owned by the caller. Callers are
responsible for calling db.session.commit() (or rollback on error).
This keeps stock changes + their history rows atomic with whatever
order/product change triggered them.
"""
from extensions import db
from models.inventory import InventoryTransaction


class InsufficientStockError(Exception):
    pass


def adjust_stock(product, quantity_change, transaction_type, seller_id=None,
                  reference_id=None, notes=None):
    """
    Apply quantity_change (can be negative) to product.stock_quantity,
    record an InventoryTransaction row, and never allow stock to go
    negative. Raises InsufficientStockError if it would.
    """
    previous_stock = product.stock_quantity
    new_stock = previous_stock + quantity_change

    if new_stock < 0:
        raise InsufficientStockError(
            f"Only {previous_stock} units are available."
        )

    product.stock_quantity = new_stock

    txn = InventoryTransaction(
        product_id=product.id,
        seller_id=seller_id or product.seller_id,
        transaction_type=transaction_type,
        quantity_change=quantity_change,
        previous_stock=previous_stock,
        new_stock=new_stock,
        reference_id=reference_id,
        notes=notes,
    )
    db.session.add(txn)
    return txn


def deduct_for_sale(product, quantity, order_number):
    if quantity > product.stock_quantity:
        raise InsufficientStockError(
            f"Only {product.stock_quantity} units of '{product.name}' are available."
        )
    return adjust_stock(
        product, -quantity, "SALE",
        reference_id=order_number,
        notes=f"Sold via order {order_number}",
    )


def restore_for_cancellation(product, quantity, order_number):
    return adjust_stock(
        product, quantity, "CANCELLATION",
        reference_id=order_number,
        notes=f"Restocked after cancellation of order {order_number}",
    )


def add_purchase_stock(product, quantity, notes=None):
    return adjust_stock(
        product, quantity, "PURCHASE",
        notes=notes or "Stock added by seller",
    )


def manual_adjustment(product, quantity_change, notes=None):
    return adjust_stock(
        product, quantity_change, "ADJUSTMENT",
        notes=notes or "Manual stock adjustment",
    )
