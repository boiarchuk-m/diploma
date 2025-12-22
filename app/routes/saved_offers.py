from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user

from app.utils.decorators import roles_required
from app.models.user import User
from app.services.users_service import UsersService
from app.services.saved_offers_service import SavedOffersService
from app.services.offers_service import OffersService

saved_offers_bp = Blueprint("saved_offers", __name__)


@saved_offers_bp.route('/saved-offers', methods=['GET'])
@login_required
def saved_offers():
    saved_offers = SavedOffersService.get_saved_offers_by_user(current_user.id)
    offers = [OffersService.get_by_id(so.offer_id) for so in saved_offers]
    offers_serialized = OffersService.serialize_multiple(offers)
    return render_template('saved_properties.html', offers=offers_serialized, is_saved=True)

@saved_offers_bp.route('/property/<int:offer_id>/save', methods=['POST'])
@login_required
def save_offer(offer_id):
    offer = OffersService.get_by_id(offer_id)
    if not offer:
        flash("Оголошення не знайдено.", "danger")
        return redirect(url_for('offers.list_properties'))

    existing = SavedOffersService.is_offer_saved(current_user.id, offer_id)
    if existing:
        flash("Оголошення вже збережено.", "info")
        return redirect(url_for('offers.property_detail', offer_id=offer_id))

    SavedOffersService.add_saved_offer(current_user.id, offer_id)
    flash("Оголошення збережено.", "success")
    return redirect(url_for('offers.property_detail', offer_id=offer_id))

@saved_offers_bp.route('/property/<int:offer_id>/unsave', methods=['POST'])
@login_required
def unsave_offer(offer_id):
    offer = OffersService.get_by_id(offer_id)
    if not offer:
        flash("Оголошення не знайдено.", "danger")
        return redirect(url_for('offers.list_properties'))

    SavedOffersService.remove_saved_offer(current_user.id, offer_id)
    flash("Оголошення видалено зі збережених.", "success")
    return redirect(url_for('offers.property_detail', offer_id=offer_id))