import os
import uuid
from datetime import datetime
from flask import current_app
from werkzeug.utils import secure_filename


def generate_order_number():
    """ORD-<year>-<6 digit sequence based on timestamp+random for uniqueness>"""
    year = datetime.utcnow().year
    unique_part = uuid.uuid4().int % 1_000_000
    return f"ORD-{year}-{unique_part:06d}"


def allowed_image_file(filename):
    if "." not in filename:
        return False
    ext = filename.rsplit(".", 1)[1].lower()
    return ext in current_app.config["ALLOWED_IMAGE_EXTENSIONS"]


def save_product_image(file_storage):
    """Validate & save an uploaded image. Returns the stored filename or None."""
    if not file_storage or file_storage.filename == "":
        return None
    if not allowed_image_file(file_storage.filename):
        raise ValueError("Invalid image type. Allowed: png, jpg, jpeg, gif, webp.")

    ext = file_storage.filename.rsplit(".", 1)[1].lower()
    safe_name = secure_filename(f"{uuid.uuid4().hex}.{ext}")
    upload_folder = current_app.config["UPLOAD_FOLDER"]
    os.makedirs(upload_folder, exist_ok=True)
    filepath = os.path.join(upload_folder, safe_name)
    file_storage.save(filepath)
    return safe_name


def delete_product_image(filename):
    if not filename:
        return
    upload_folder = current_app.config["UPLOAD_FOLDER"]
    filepath = os.path.join(upload_folder, filename)
    if os.path.exists(filepath):
        try:
            os.remove(filepath)
        except OSError:
            pass


def format_currency(amount):
    try:
        amount = float(amount)
    except (TypeError, ValueError):
        amount = 0.0
    symbol = current_app.config.get("CURRENCY_SYMBOL", "\u20b9")
    return f"{symbol}{amount:,.2f}"
