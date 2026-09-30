import os
from urllib.parse import quote_plus
from dotenv import load_dotenv
from urllib.parse import quote_plus
load_dotenv()

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-me")

    DB_HOST = os.environ.get("DB_HOST", "localhost")
    DB_PORT = os.environ.get("DB_PORT", "3306")
    DB_NAME = os.environ.get("DB_NAME", "inventory_system")
    DB_USER = os.environ.get("DB_USER", "root")
    DB_PASSWORD = os.environ.get("DB_PASSWORD", "@Harshal9331")



    SQLALCHEMY_DATABASE_URI = (
    f"mysql+pymysql://{quote_plus(DB_USER)}:{quote_plus(DB_PASSWORD)}"
    f"@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": 280,
    }

    # Uploads
    UPLOAD_FOLDER = os.path.join(BASE_DIR, "static", "uploads")
    ALLOWED_IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}
    MAX_UPLOAD_MB = int(os.environ.get("MAX_UPLOAD_MB", 3))
    MAX_CONTENT_LENGTH = MAX_UPLOAD_MB * 1024 * 1024

    # Session / cookies
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    REMEMBER_COOKIE_DURATION = 60 * 60 * 24 * 7  # 7 days

    # Business rules
    ITEMS_PER_PAGE = 12
    ORDERS_PER_PAGE = 15
    CANCELLABLE_STATUSES = {"Pending", "Confirmed", "Packed"}
    STATUS_FLOW = ["Pending", "Confirmed", "Packed", "Shipped", "Delivered"]
    CURRENCY_SYMBOL = "\u20b9"
