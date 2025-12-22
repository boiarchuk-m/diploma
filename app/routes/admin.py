from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user

from app.services.admin_service import AdminService
from app.services.offers_service import OffersService
from app.utils.decorators import roles_required
from app.models.user import User

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

@admin_bp.route("/pending", methods=["GET"])
@login_required
@roles_required(User.ROLE_ADMIN)
def pending():
    if current_user.role != User.ROLE_ADMIN:
        flash("Доступ заборонено", "danger")
        return redirect(url_for("offers.index"))

    offers = AdminService.get_pending_offers()

    offers_view = OffersService.serialize_multiple(offers)

    return render_template("admin/pending.html", offers=offers_view)


@admin_bp.route("/offer/<int:offer_id>", methods=["GET"])
@login_required
@roles_required(User.ROLE_ADMIN)
def review_offer(offer_id: int):
    if current_user.role != User.ROLE_ADMIN:
        flash("Доступ заборонено", "danger")
        return redirect(url_for("offers.index"))

    offer = AdminService.get_offer(offer_id)
    if not offer:
        flash("Оголошення не знайдено", "warning")
        return redirect(url_for("admin.pending"))

    offer_view = OffersService.serialize_offer(offer)
    return render_template("admin/review_offer.html", offer=offer_view)

@admin_bp.route("/offer/<int:offer_id>/comment", methods=["POST"])
@login_required
@roles_required(User.ROLE_ADMIN)
def comment_offer(offer_id: int):
    if current_user.role != User.ROLE_ADMIN:
        flash("Доступ заборонено", "danger")
        return redirect(url_for("offers.index"))

    comment = request.form.get("admin_comment", "")
    AdminService.add_comment(offer_id, comment)
    flash("Коментар збережено", "success")
    return redirect(url_for("admin.review_offer", offer_id=offer_id))

@admin_bp.route("/offer/<int:offer_id>/approve", methods=["POST"])
@login_required
@roles_required(User.ROLE_ADMIN)
def approve_offer(offer_id: int):
    if current_user.role != User.ROLE_ADMIN:
        flash("Доступ заборонено", "danger")
        return redirect(url_for("offers.index"))

    comment = request.form.get("admin_comment")
    AdminService.approve_offer(offer_id, comment=comment)
    flash("Оголошення підтверджено", "success")
    return redirect(url_for("admin.pending"))

@admin_bp.route("/offer/<int:offer_id>/delete", methods=["POST"])
@login_required
@roles_required(User.ROLE_ADMIN)
def delete_offer(offer_id: int):
    if current_user.role != User.ROLE_ADMIN:
        flash("Доступ заборонено", "danger")
        return redirect(url_for("offers.index"))

    offer = AdminService.get_offer(offer_id)
    if not offer:
        flash("Оголошення не знайдено", "warning")
        return redirect(url_for("admin.pending"))

    OffersService.delete_offer(offer)
    flash("Оголошення видалено", "success")
    return redirect(url_for("admin.pending"))