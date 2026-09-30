import re
from decimal import Decimal, InvalidOperation

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
PHONE_RE = re.compile(r"^[0-9+\-\s]{7,15}$")
PINCODE_RE = re.compile(r"^[0-9]{4,10}$")


def is_valid_email(email):
    return bool(email) and bool(EMAIL_RE.match(email.strip()))


def is_valid_phone(phone):
    return bool(phone) and bool(PHONE_RE.match(phone.strip()))


def is_valid_pincode(pincode):
    return bool(pincode) and bool(PINCODE_RE.match(pincode.strip()))


def parse_positive_decimal(value, allow_zero=False):
    """Return a Decimal >= 0 (or > 0) or None if invalid."""
    try:
        d = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return None
    if d < 0:
        return None
    if not allow_zero and d == 0:
        return None
    return d


def parse_non_negative_int(value):
    try:
        i = int(value)
    except (TypeError, ValueError):
        return None
    if i < 0:
        return None
    return i


def clean_str(value, max_len=None):
    if value is None:
        return ""
    v = value.strip()
    if max_len:
        v = v[:max_len]
    return v
