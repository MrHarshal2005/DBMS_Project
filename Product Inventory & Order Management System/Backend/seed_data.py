"""
Seed the database with sample sellers, buyers, categories, products and
orders so the application can be explored immediately after setup.

Usage:
    python seed_data.py
"""
import random
from datetime import datetime, timedelta

from app import create_app
from extensions import db
from models.user import User
from models.category import Category
from models.product import Product
from models.order import Order, OrderItem
from models.inventory import InventoryTransaction
from utils.helpers import generate_order_number

app = create_app()


def run():
    with app.app_context():
        db.drop_all()
        db.create_all()

        # ---------------------------------------------------------- users
        sellers = [
            User(name="Rajesh Kumar", email="seller1@example.com", phone="9876543210",
                 role="SELLER", status="ACTIVE"),
            User(name="Priya Sharma", email="seller2@example.com", phone="9876543211",
                 role="SELLER", status="ACTIVE"),
        ]
        for s in sellers:
            s.set_password("Seller@123")
        db.session.add_all(sellers)

        buyers = [
            User(name="Amit Verma", email="buyer1@example.com", phone="9123456780",
                 role="BUYER", status="ACTIVE"),
            User(name="Sneha Reddy", email="buyer2@example.com", phone="9123456781",
                 role="BUYER", status="ACTIVE"),
            User(name="Karan Singh", email="buyer3@example.com", phone="9123456782",
                 role="BUYER", status="ACTIVE"),
        ]
        for b in buyers:
            b.set_password("Buyer@123")
        db.session.add_all(buyers)
        db.session.commit()

        # ----------------------------------------------------- categories
        category_names = [
            ("Electronics", "Gadgets, devices and accessories"),
            ("Clothing", "Apparel for men, women and kids"),
            ("Grocery", "Everyday food and household essentials"),
            ("Furniture", "Home and office furniture"),
            ("Accessories", "Bags, watches and other accessories"),
        ]
        categories = [Category(name=n, description=d, status="ACTIVE")
                      for n, d in category_names]
        db.session.add_all(categories)
        db.session.commit()

        cat = {c.name: c for c in categories}

        # ------------------------------------------------------- products
        product_defs = [
            ("Wireless Mouse", "Electronics", 599, 50, 10, 0),
            ("Bluetooth Headphones", "Electronics", 1999, 30, 5, 0),
            ("USB-C Charger 30W", "Electronics", 899, 40, 8, 0),
            ("27-inch Monitor", "Electronics", 15999, 12, 3, 0),
            ("Mechanical Keyboard", "Electronics", 3499, 20, 5, 0),
            ("Men's Cotton T-Shirt", "Clothing", 499, 100, 20, 1),
            ("Women's Denim Jacket", "Clothing", 2199, 25, 5, 1),
            ("Kids Hoodie", "Clothing", 899, 40, 10, 1),
            ("Running Shoes", "Clothing", 2999, 35, 8, 1),
            ("Basmati Rice 5kg", "Grocery", 549, 80, 15, 0),
            ("Organic Honey 500g", "Grocery", 349, 60, 10, 0),
            ("Green Tea Pack (100 bags)", "Grocery", 299, 70, 15, 1),
            ("Office Chair", "Furniture", 5999, 15, 3, 0),
            ("Wooden Study Table", "Furniture", 7499, 3, 5, 1),
            ("Bookshelf 5-Tier", "Furniture", 4299, 10, 2, 0),
            ("Leather Wallet", "Accessories", 799, 45, 10, 1),
            ("Analog Wrist Watch", "Accessories", 2499, 22, 5, 0),
            ("Travel Backpack", "Accessories", 1899, 2, 5, 1),
        ]

        products = []
        for i, (name, cat_name, price, stock, min_stock, seller_idx) in enumerate(product_defs):
            p = Product(
                seller_id=sellers[seller_idx].id,
                category_id=cat[cat_name].id,
                name=name,
                sku=f"SKU-{1000 + i}",
                description=f"High quality {name.lower()} available at a great price.",
                price=price,
                stock_quantity=stock,
                minimum_stock=min_stock,
                status="ACTIVE",
            )
            products.append(p)
        db.session.add_all(products)
        db.session.commit()

        for p in products:
            db.session.add(InventoryTransaction(
                product_id=p.id, seller_id=p.seller_id, transaction_type="PURCHASE",
                quantity_change=p.stock_quantity, previous_stock=0,
                new_stock=p.stock_quantity, notes="Initial seed stock",
            ))
        db.session.commit()

        # --------------------------------------------------------- orders
        statuses = ["Pending", "Confirmed", "Packed", "Shipped", "Delivered", "Cancelled"]
        sample_addresses = [
            ("Amit Verma", "9123456780", "buyer1@example.com", "221B Residency Road",
             "Bengaluru", "Karnataka", "560025"),
            ("Sneha Reddy", "9123456781", "buyer2@example.com", "45 Jubilee Hills",
             "Hyderabad", "Telangana", "500033"),
            ("Karan Singh", "9123456782", "buyer3@example.com", "12 Connaught Place",
             "New Delhi", "Delhi", "110001"),
        ]

        for idx, status in enumerate(statuses):
            buyer = buyers[idx % len(buyers)]
            addr = sample_addresses[idx % len(sample_addresses)]
            chosen_products = random.sample(products, k=random.randint(1, 3))
            order_number = generate_order_number()

            order = Order(
                order_number=order_number,
                buyer_id=buyer.id,
                seller_id=chosen_products[0].seller_id,
                payment_method="COD",
                payment_status="PAID" if status == "Delivered" else "PENDING",
                order_status=status,
                delivery_name=addr[0], delivery_phone=addr[1], delivery_email=addr[2],
                delivery_address=addr[3], delivery_city=addr[4], delivery_state=addr[5],
                delivery_pincode=addr[6],
                created_at=datetime.utcnow() - timedelta(days=random.randint(0, 20)),
                total_amount=0,
            )
            db.session.add(order)
            db.session.flush()

            total = 0
            for p in chosen_products:
                if p.seller_id != chosen_products[0].seller_id:
                    continue
                qty = random.randint(1, 3)
                subtotal = float(p.price) * qty
                total += subtotal
                db.session.add(OrderItem(
                    order_id=order.id, product_id=p.id, product_name=p.name,
                    quantity=qty, unit_price=p.price, subtotal=subtotal,
                ))
                if status != "Cancelled":
                    p.stock_quantity = max(0, p.stock_quantity - qty)
                    db.session.add(InventoryTransaction(
                        product_id=p.id, seller_id=p.seller_id, transaction_type="SALE",
                        quantity_change=-qty, previous_stock=p.stock_quantity + qty,
                        new_stock=p.stock_quantity, reference_id=order_number,
                        notes=f"Seed sale via {order_number}",
                    ))
            order.total_amount = total
            db.session.commit()

        print("Database seeded successfully.")
        print("\nSample credentials:")
        print("  Seller 1: seller1@example.com / Seller@123")
        print("  Seller 2: seller2@example.com / Seller@123")
        print("  Buyer 1:  buyer1@example.com  / Buyer@123")
        print("  Buyer 2:  buyer2@example.com  / Buyer@123")
        print("  Buyer 3:  buyer3@example.com  / Buyer@123")


if __name__ == "__main__":
    run()
