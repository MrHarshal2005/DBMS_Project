from functools import wraps
from flask import abort, flash, redirect, url_for
from flask_login import current_user


def seller_required(view_func):
    """Only logged-in users with role SELLER may access."""
    @wraps(view_func)
    def wrapped(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for("auth.login"))
        if not current_user.is_seller():
            flash("You are not authorized to perform this action.", "danger")
            return abort(403)
        return view_func(*args, **kwargs)
    return wrapped


def buyer_required(view_func):
    """Only logged-in users with role BUYER may access."""
    @wraps(view_func)
    def wrapped(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for("auth.login"))
        if not current_user.is_buyer():
            flash("You are not authorized to perform this action.", "danger")
            return abort(403)
        return view_func(*args, **kwargs)
    return wrapped
