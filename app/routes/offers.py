from app import db
from app.models.business_type import Business_type
from app.models.user import User
from flask_login import login_required, current_user
from app.utils.decorators import roles_required
from app.utils.files import allowed_file, unique_filename
from app.services.offers_service import OffersService
from flask import flash, redirect, session
from flask import render_template, request, jsonify, url_for, Blueprint
from app.services.saved_offers_service import SavedOffersService


offers_bp = Blueprint("offers", __name__)

@offers_bp.route('/')
def index():
    return render_template ('main.html')


@offers_bp.route('/properties', methods=['GET'])
def list_properties():
    offers = OffersService.get_all()
    offers_serialized = OffersService.serialize_multiple(offers)

    return render_template("properties.html", offers=offers_serialized)

@offers_bp.route("/properties/filter", methods=["POST"])
def filter_properties():
    """
    Приймає фільтри через JSON (AJAX)
    і повертає JSON відповідь.
    """

    payload = request.get_json() or {}

    filters = {
        "min_price": request.args.get("min_price", type=int),
        "max_price": request.args.get("max_price", type=int),
        "min_area": request.args.get("min_area", type=int),
        "max_area": request.args.get("max_area", type=int),
        "districts": request.args.getlist("districts"),
        "repair_types": request.args.getlist("repair_types"),
        "sort": request.args.get("sort")
    }

    offers = OffersService.get_all()
    serialized = OffersService.serialize_multiple(offers)

    filtered = OffersService.filter_offers(serialized, filters)

    return jsonify(filtered)


@offers_bp.route('/property/<int:offer_id>', methods=['GET'])
def property_detail(offer_id):
    offer = OffersService.get_by_id(offer_id)
    if not offer:
        flash("Оголошення не знайдено.", "danger")
        return redirect(url_for('offers.list_properties'))

    offer_serialized = OffersService.serialize_offer(offer)

    ranking_results = session.get("ranking_results", {})
    extra = ranking_results.get(str(offer_id))
    if extra:
        offer_serialized["ranking"] = extra.get("rank")
        offer_serialized["competitors_count"] = extra.get("competitors_count")
        offer_serialized["other_businesses_count"] = extra.get("other_businesses_count")
    #print(offer_serialized["competitors_count"])
    is_saved = False
    if current_user.is_authenticated:
        is_saved = SavedOffersService.is_offer_saved(current_user.id, offer_id)

    return render_template('property_detail.html', offer=offer_serialized, is_saved=is_saved)



@offers_bp.route('/property/create', methods=['GET', 'POST'])
@roles_required(User.ROLE_LANDLORD)
def create_property():

    business_types = Business_type.query.all()
    business_types_serialized = [bt.serialize() for bt in business_types]

    if request.method == 'POST':
        address=request.form.get('address') or ""
        district = request.form.get('district') or ""
        city = request.form.get('city') or ""
        price = request.form.get('price')
        area = request.form.get('area')
        description = request.form.get('description') or ""
        repair = request.form.get('repair') or "" 
        if not address or not district or not price or not area:
            flash("Будь ласка, заповніть обовʼязкові поля", "danger")
            return render_template("property_form.html", offer=None, photos_serialized=[], business_types=business_types_serialized)
        
        try:
            data = {
                "address": address,
                "district": district,
                "city": city,
                "price": int(float(price)),
                "area": int(float(area)),
                "description": description,
                "repair": repair,
            }

            recommended_ids = []
            for tid in request.form.getlist("recommended_types"):
                try:
                    recommended_ids.append(int(tid))
                except ValueError:
                    continue
            
            offer = OffersService.create_offer_full(
                data=data,
                owner_id=current_user.id,
                recommended_type_ids=recommended_ids,
                files=request.files.getlist("photos"),
                allowed_file=allowed_file,
                unique_filename=unique_filename
            )

            flash("Оголошення успішно створено", "success")
            return redirect(url_for("offers.property_detail", offer_id=offer.id))

        except ValueError:
            flash("Невірний формат числових полів", "danger")

    return render_template("property_form.html", offer=None,
                           photos_serialized=[], business_types=business_types_serialized)



@offers_bp.route('/property/<int:offer_id>/edit', methods=['GET', 'POST'])
@roles_required(User.ROLE_LANDLORD)
def edit_property(offer_id):
    offer = OffersService.get_by_id(offer_id)
    if not offer:
        flash("Оголошення не знайдено.", "danger")
        return redirect(url_for('offers.list_properties'))

    if offer.owner_id != current_user.id:
        if current_user.role != User.ROLE_ADMIN:
            flash("Ви не маєте прав на редагування цього оголошення.", "danger")
            return redirect(url_for('offers.property_detail', offer_id=offer_id))

    photos_serialized = [p.serialize() for p in offer.offer_photos]

    business_types = Business_type.query.all()
    business_types_serialized = [bt.serialize() for bt in business_types]
    current_recommended = [rb.type_id for rb in offer.recommended_businesses]

    if request.method == 'POST':
        address=request.form.get('address') or ""
        district = request.form.get('district') or ""
        city = request.form.get('city') or ""
        price = request.form.get('price')
        area = request.form.get('area')
        description = request.form.get('description') or ""
        repair = request.form.get('repair') or "" 

        if not address or not district or not price or not area:
            flash("Будь ласка, заповніть обовʼязкові поля", "danger")
            return render_template('property_form.html', offer=offer, 
                                   photos_serialized=photos_serialized, 
                                   business_types=business_types_serialized,
                                   current_recommended=current_recommended)
        
        try:
            data = {
                "address": address,
                "district": district,
                "city": city,
                "price": int(float(price)),
                "area": float(area),
                "description": description,
                "repair": repair,
            }

            recommended_ids = []
            for tid in request.form.getlist("recommended_types"):
                try:
                    recommended_ids.append(int(tid))
                except ValueError:
                    continue

            OffersService.update_offer_full(
                offer=offer,
                data=data,
                recommended_type_ids=recommended_ids,
                files=request.files.getlist("photos"),
                delete_photo_ids=request.form.getlist("delete_photos"),
                new_primary_id=request.form.get("primary_photo"),
                allowed_file=allowed_file,
                unique_filename=unique_filename
            )

            flash("Оголошення успішно оновлено (потребує повторного підтвердження)", "success")
            return redirect(url_for("offers.property_detail", offer_id=offer.id))

        except ValueError:
            flash("Невірний формат числових полів", "danger")

    return render_template("property_form.html",
                           offer=offer,
                           photos_serialized=photos_serialized,
                           business_types=business_types_serialized,
                           current_recommended=current_recommended)

    
@offers_bp.route('/my-properties', methods=['GET'])
@login_required
@roles_required(User.ROLE_LANDLORD)
def my_properties():
    offers = OffersService.get_offers_by_owner(current_user.id)
    serialized = OffersService.serialize_multiple(offers)
    total = len(offers)
    approved = sum(1 for o in offers if getattr(o, 'approved', False))
    pending = total - approved
    return render_template('my_properties.html', offers=serialized, total=total, approved=approved, pending=pending)


@offers_bp.route('/property/<int:offer_id>/delete', methods=['POST'])
@roles_required(User.ROLE_LANDLORD, User.ROLE_ADMIN) 
def delete_property(offer_id):
    offer = OffersService.get_by_id(offer_id)
    if not offer:
        flash("Оголошення не знайдено.", "danger")
        return redirect(url_for('offers.list_properties'))

    if offer.owner_id != current_user.id:
        if current_user.role != User.ROLE_ADMIN:
            flash("Ви не маєте прав на видалення цього оголошення.", "danger")
            return redirect(url_for('offers.property_detail', offer_id=offer_id))


    OffersService.delete_offer(offer)

    flash("Оголошення успішно видалено.", "success")
    return redirect(url_for('offers.my_properties'))

