# InventoryHub &mdash; Seller-Buyer Inventory & Order Management System

A complete, functional web application for multi-seller inventory and order
management, built with Flask, MySQL and Bootstrap 5.

## Features

**Sellers** can register, manage products & categories, track inventory with
full transaction history, view/update buyer orders through a controlled
status flow, see low-stock alerts, and view sales reports.

**Buyers** can register, browse/search/filter/sort products, manage a
shopping cart, check out with Cash on Delivery, track orders, cancel
eligible orders, and manage their profile.

Core guarantees:
- Passwords are hashed with Werkzeug (never stored in plain text).
- Session-based auth with role-based access control (sellers and buyers are
  strictly separated; a seller can never touch another seller's products).
- All price/stock/total calculations happen server-side; nothing from the
  browser is trusted.
- Every stock change (sale, cancellation, purchase, manual adjustment) is
  recorded in `inventory_transactions` and applied inside a DB transaction
  so stock can never go negative or become inconsistent.
- Order status only moves forward one step at a time (Pending → Confirmed →
  Packed → Shipped → Delivered), or to Cancelled while still eligible.

## Technology Stack

- Frontend: HTML5, CSS3, JavaScript, Bootstrap 5
- Backend: Python, Flask
- Database: MySQL, via SQLAlchemy + PyMySQL
- Auth: Flask-Login (session-based) + Werkzeug password hashing
- CSRF protection: Flask-WTF

## Project Structure

```
inventory_order_system/
├── app.py                 # App factory, blueprint registration, error handlers
├── config.py               # Configuration loaded from .env
├── extensions.py           # db / login_manager / csrf singletons
├── schema.sql               # Explicit MySQL DDL (optional/manual reference)
├── seed_data.py             # Sample data seeding script
├── requirements.txt
├── .env.example
├── models/                  # SQLAlchemy models
├── routes/                  # Flask blueprints (auth, buyer, seller, products, cart, orders)
├── templates/                # Jinja2 templates (Bootstrap 5)
├── static/                    # css/js/images/uploads
└── utils/                     # auth decorators, validators, helpers, inventory_service
```

## Requirements

- Python 3.10+
- MySQL 8.0+ (or MariaDB 10.5+)
- pip / virtualenv

## Setup

### 1. Clone / unzip the project and enter the folder

```bash
cd inventory_order_system
```

### 2. Create and activate a virtual environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Create the MySQL database

```sql
CREATE DATABASE inventory_system CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

You do **not** need to run `schema.sql` manually — the seed script below
creates all tables automatically via SQLAlchemy. `schema.sql` is provided
as an explicit, reviewable reference of the schema (and for manual/
production setups where you prefer running DDL yourself).

### 5. Configure environment variables

```bash
cp .env.example .env
```

Edit `.env` and set your real database credentials:

```
SECRET_KEY=replace_with_a_long_random_string
DB_HOST=localhost
DB_PORT=3306
DB_NAME=inventory_system
DB_USER=root
DB_PASSWORD=your_mysql_password
```

### 6. Seed sample data (creates tables + sample sellers/buyers/products/orders)

```bash
python seed_data.py
```

This will **drop and recreate all tables**, so only run it on a fresh/dev
database. It prints sample login credentials when done.

### 7. Run the application

```bash
python app.py
```

Visit **http://localhost:5000** in your browser.

## Sample Login Credentials

| Role     | Email                | Password    |
|----------|-----------------------|------------|
| Seller 1 | seller1@example.com  | Seller@123 |
| Seller 2 | seller2@example.com  | Seller@123 |
| Buyer 1  | buyer1@example.com   | Buyer@123  |
| Buyer 2  | buyer2@example.com   | Buyer@123  |
| Buyer 3  | buyer3@example.com   | Buyer@123  |

## Key Workflows to Try

1. Log in as a seller → **Add Product** → set stock/price/category.
2. Log out, register/log in as a buyer → browse **Shop** → open a product
   → **Add to Cart**.
3. Go to **Cart** → adjust quantity → **Proceed to Checkout** → fill
   delivery details → **Place Order** (stock is deducted immediately,
   an `inventory_transactions` row of type `SALE` is created).
4. Log back in as the seller → **Orders** → open the order → **Mark as
   Confirmed** → **Packed** → **Shipped** → **Delivered** (status can only
   move forward one step at a time).
5. As the buyer, cancel an order before it ships from **My Orders** →
   order detail → **Cancel Order** (stock is automatically restored, a
   `CANCELLATION` transaction is logged).
6. As the seller, check **Inventory** for the full stock ledger, and
   **Reports** for sales/best-sellers/low-stock over a date range.

## Security Notes

- Never trust client-submitted `price`, `stock`, `seller_id`, or
  `total_amount` values — all of these are recalculated or re-validated
  server-side in `routes/orders.py` and `routes/seller.py`.
- File uploads are restricted by extension (`png`, `jpg`, `jpeg`, `gif`,
  `webp`), renamed with a random UUID via `secure_filename`, and capped by
  `MAX_UPLOAD_MB` in `.env`.
- CSRF protection is enabled globally via Flask-WTF.
- All ORM queries use SQLAlchemy's parameter binding (no raw string-built
  SQL), which protects against SQL injection.

## Troubleshooting

**`sqlalchemy.exc.OperationalError: (pymysql.err.OperationalError) (1045, ...)`**
Your `DB_USER` / `DB_PASSWORD` in `.env` don't match your MySQL setup.
Verify you can log in with `mysql -u <user> -p`.

**`(1049, "Unknown database 'inventory_system'")`**
You haven't created the database yet — run the `CREATE DATABASE` statement
in step 4.

**`ModuleNotFoundError: No module named 'flask_sqlalchemy'` (or similar)**
Your virtual environment isn't activated, or dependencies weren't
installed — re-run `pip install -r requirements.txt` inside the activated
venv.

**Images not showing after upload**
Confirm `static/uploads/` exists and is writable; it's created
automatically on first upload if missing.

**Port 5000 already in use**
Run `python app.py` after editing the last line of `app.py` to use a
different port, e.g. `app.run(debug=True, port=5001)`.

## Extending to Online Payments

The system is structured so a payment gateway can be added later without
schema changes: `orders.payment_method` and `orders.payment_status` already
exist and default to `COD` / `PENDING`. To add a gateway, you would add a
new payment route/service that, on success, sets `payment_status = 'PAID'`
before or after order creation, following the same flow used in
`routes/orders.py::checkout`.
