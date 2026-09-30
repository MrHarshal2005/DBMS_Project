from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user

from extensions import db
from models.order import Order
from utils.auth import buyer_required
from utils.validators import is_valid_email, is_valid_phone, clean_str

buyer_bp = Blueprint("buyer", __name__)


@buyer_bp.route("/buyer/dashboard")
@login_required
@buyer_required
def dashboard():
    recent_orders = (Order.query.filter_by(buyer_id=current_user.id)
                      .order_by(Order.created_at.desc()).limit(5).all())
    total_orders = Order.query.filter_by(buyer_id=current_user.id).count()
    pending_orders = Order.query.filter_by(
        buyer_id=current_user.id).filter(
        Order.order_status.in_(["Pending", "Confirmed", "Packed", "Shipped"])).count()
    delivered_orders = Order.query.filter_by(
        buyer_id=current_user.id, order_status="Delivered").count()

    return render_template(
        "buyer/dashboard.html",
        recent_orders=recent_orders,
        total_orders=total_orders,
        pending_orders=pending_orders,
        delivered_orders=delivered_orders,
    )


@buyer_bp.route("/profile", methods=["GET", "POST"])
@login_required
@buyer_required
def profile():
    if request.method == "POST":
        name = clean_str(request.form.get("name"), 120)
        phone = clean_str(request.form.get("phone"), 20)

        errors = []
        if not name:
            errors.append("Name is required.")
        if phone and not is_valid_phone(phone):
            errors.append("Please enter a valid phone number.")

        if errors:
            for e in errors:
                flash(e, "danger")
        else:
            current_user.name = name
            current_user.phone = phone
            db.session.commit()
            flash("Profile updated successfully.", "success")
        return redirect(url_for("buyer.profile"))

    return render_template("buyer/profile.html")


@buyer_bp.route("/profile/change-password", methods=["POST"])
@login_required
@buyer_required
def change_password():
    current_password = request.form.get("current_password") or ""
    new_password = request.form.get("new_password") or ""
    confirm_password = request.form.get("confirm_password") or ""

    if not current_user.check_password(current_password):
        flash("Current password is incorrect.", "danger")
    elif len(new_password) < 6:
        flash("New password must be at least 6 characters long.", "danger")
    elif new_password != confirm_password:
        flash("New passwords do not match.", "danger")
    else:
        current_user.set_password(new_password)
        db.session.commit()
        flash("Password changed successfully.", "success")

    return redirect(url_for("buyer.profile"))
