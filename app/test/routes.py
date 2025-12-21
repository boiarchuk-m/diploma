from app import db
import os
from app.test import test
from app.models.comm_leasing import CommLeasing
from app.models.business_type import Business_type
from app.models.nearby_business import NearbyBusiness
from app.models.num_businesses import NumBusinesses
from app.models.offer_photo import OfferPhoto
from app.services.auth_service import AuthService
from app.models.user import User
from flask_login import login_user, logout_user, login_required, current_user
from app.services.users_service import UsersService
from app.utils.decorators import roles_required
from app.utils.files import allowed_file, unique_filename
from app.models.recommended_business import RecommendedBusiness

import json
from flask import Response, flash, redirect, session, current_app
from flask import render_template, request, jsonify, url_for
import math
from app.services.ranking_service import RankingService
from app.services.offers_service import OffersService
from app.services.onboarding_service import OnboardingService



@test.route('/')
def index():
    return render_template ('main.html')


@test.route('/onboarding')
def onboarding():
    """Форма онбордингу - вибір параметрів для ранжування."""
    data = OffersService.get_initial_data()
    return render_template("onboarding.html",   
                           categories = data["categories"],
                           districts = data["districts"],
                           cities = data["cities"]
                           )


@test.route("/onboarding/offers", methods=["POST"])
def onboarding_submit():
    data = request.get_json(silent=True)
    if not data and request.form.get('payload'):
        data = json.loads(request.form['payload'])
    raw = data or {}
        
    user_choice = {
            "business_type": raw.get("business_type"),
            "business_type_id": raw.get("business_type_id"),
            "area": {
                "min": raw.get("area", {}).get("min"),
                "max": raw.get("area", {}).get("max")
            },
            "preferred_districts": raw.get("districts", []),
            "city": raw.get("city"),
    }

    session["user_choice"] = user_choice

    return redirect(url_for('test.list_ranked_properties'))


@test.route('/properties/ranked', methods=['GET'])
def list_ranked_properties():

    user_choice = session.get("user_choice", {})

    #offer_ids, ranking_results = OnboardingService.run_ranking(user_choice)
    results = RankingService(user_choice).run()

    offers_for_view = OffersService.build_ranked_offers(results)

    #offers_for_view = OnboardingService.build_ranked_offers(offer_ids, ranking_results)

    return render_template('properties_onb.html', offers=offers_for_view)


@test.route('/properties', methods=['GET'])
def list_properties():
    offers = OffersService.get_all()
    offers_serialized = OffersService.serialize_multiple(offers)


    #filtered = OffersService.filter_offers(offers_serialized, filters)
    return render_template("properties.html", offers=offers_serialized)
    #return render_template('properties.html', offers=filtered, filters=filters)

@test.route("/properties/filter", methods=["POST"])
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


@test.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        data = request.form
        email = data.get('email').strip()
        password = data.get('password', "")
        role_type = data.get('role_type', 'tenant')
        print(role_type)

        if role_type == "landlord":
            role = User.ROLE_LANDLORD
        else:
            role = User.ROLE_TENANT

        try:
            user = AuthService.register_user(email, password, role)
        except ValueError as e:
            flash(str(e), "danger")
            return render_template("register.html")
        
        flash("Реєстрація успішна. Ви увійшли в систему.", "success")
        login_user(user)

        if user.role == User.ROLE_LANDLORD:
            return redirect(url_for("test.edit_profile"))
        else:
            print("Redirecting tenant to main page")
            return redirect(url_for("test.index"))

    return render_template('register.html')


@test.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.form
        email = data.get('email').strip()
        password = data.get('password', "")

        user = AuthService.authenticate_user(email, password)
        if not user:
            flash("Невірний email або пароль.", "danger")
            return render_template("login.html", form_data={'email': email})
        
        login_user(user)
        flash("Вхід успішний.", "success")

        return redirect(url_for("test.index"))


    return render_template('login.html', form_data={})
    

@test.route('/logout')
@login_required
def logout():
    logout_user()
    flash("Ви вийшли з системи.", "success")
    return redirect(url_for('test.index'))


@test.route('/profile', methods=['GET'])
@login_required
def profile_view():
    return render_template('profile_view.html', user=current_user)


@test.route('/profile/edit', methods=['GET', 'POST'])
@roles_required(User.ROLE_LANDLORD)

def edit_profile():
    if request.method == 'POST':
        data= {
            'first_name': request.form.get('first_name'),
            'last_name': request.form.get('last_name'),
            'phone_number': request.form.get('phone_number'),
            'company_name': request.form.get('company_name'),
            'contact_telegram': bool(request.form.get('contact_telegram')),
            'contact_viber': bool(request.form.get('contact_viber')),
            'contact_whatsapp': bool(request.form.get('contact_whatsapp')),
        }

        user = UsersService.update_profile(current_user, data)
        flash("Профіль оновлено успішно.", "success")
        return redirect(url_for('test.index'))
    return render_template('profile.html', user=current_user)


@test.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    if request.method == 'POST':
        current_password = request.form.get('current_password', "")
        new_password = request.form.get('new_password', "")
        confirm_password = request.form.get('confirm_password', "")

        if not request.user.check_password(current_password):
            flash("Поточний пароль невірний.", "danger")
            return render_template('change_password.html')

        if new_password != confirm_password:
            flash("Новий пароль та підтвердження не співпадають.", "danger")
            return render_template('change_password.html', user=current_user)

        try:
            UsersService.change_password(
                request.user, 
                current_password, 
                new_password, 
                confirm_password)
        except ValueError as e:
            flash(str(e), "danger")
            return render_template('password.html', user=current_user)
        flash("Пароль успішно змінено.", "success")

        return redirect(url_for('test.profile_view'))

    return render_template('password.html', user=current_user)


@test.route('/change_role', methods=['POST'])
@login_required
def change_role():
    new_role = request.form.get('new_role', "")
    try:
        UsersService.change_role(request.user, new_role)
    except ValueError as e:
        flash(str(e), "danger")
        return redirect(url_for('test.edit_profile'))

    flash("Роль успішно змінена.", "success")
    return redirect(url_for('test.index'))


@test.route('/property/<int:offer_id>', methods=['GET'])
def property_detail(offer_id):
    offer = OffersService.get_by_id(offer_id)
    if not offer:
        flash("Оголошення не знайдено.", "danger")
        return redirect(url_for('test.list_properties'))

    offer_serialized = OffersService.serialize_offer(offer)

    ranking_results = session.get("ranking_results", {})
    extra = ranking_results.get(str(offer_id))
    if extra:
        offer_serialized["ranking"] = extra.get("rank")
        offer_serialized["competitors_count"] = extra.get("competitors_count")
        offer_serialized["other_businesses_count"] = extra.get("other_businesses_count")
    
    return render_template('property_detail.html', offer=offer_serialized)



@test.route('/property/create', methods=['GET', 'POST'])
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
            return render_template("property_form.html", offer=None)
        
        print(price)
        try:
            data = {
                "address": address,
                "district": district,
                "city": city,
                "price": int(price),
                "area": float(area),
                "description": description,
                "repair": repair,
            }
            offer = OffersService.create_offer(data, owner_id=current_user.id)

            recommended_types = request.form.getlist('recommended_types')
            for type_id in recommended_types:
                try:
                    type_id_int = int(type_id)
                    rec = RecommendedBusiness(listing_id=offer.id, type_id=type_id_int)
                    db.session.add(rec)
                except ValueError:
                    continue


            # --- робота з фото ---
            files = request.files.getlist("photos")
            saved_any = False

            for idx, file in enumerate(files):
                if not file or file.filename == "":
                    continue
                if not allowed_file(file.filename):
                    continue

                filename = unique_filename(file.filename)
                upload_folder = current_app.config["UPLOAD_FOLDER"]
                file_path = os.path.join(upload_folder, filename)
                file.save(file_path)

                # шлях, який будемо зберігати в БД (відносно static)
                relative_path = os.path.join("photos", filename).replace("\\", "/")

                photo = OfferPhoto(
                    offer_id=offer.id,
                    photo_url=relative_path,
                    is_primary=(idx == 0)
                )
                db.session.add(photo)
                saved_any = True

            db.session.commit()

            flash("Оголошення успішно створено", "success")
            return redirect(url_for("test.property_detail", offer_id=offer.id))

        except ValueError:
            flash("Невірний формат числових полів", "danger")


    return render_template('property_form.html', offer=None, photos_serialized=[], business_types=business_types_serialized)


@test.route('/property/<int:offer_id>/edit', methods=['GET', 'POST'])
@roles_required(User.ROLE_LANDLORD)
def edit_property(offer_id):
    offer = OffersService.get_by_id(offer_id)
    if not offer:
        flash("Оголошення не знайдено.", "danger")
        return redirect(url_for('test.list_properties'))

    if offer.owner_id != current_user.id:
        if current_user.role != User.ROLE_ADMIN:
            flash("Ви не маєте прав на редагування цього оголошення.", "danger")
            return redirect(url_for('test.property_detail', offer_id=offer_id))

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
            return render_template('property_form.html', offer=offer, photos_serialized=photos_serialized)
        try:
            # Use float first for price to handle '100.0', then int
            price_val = int(float(price))
            area_val = int(float(area))
        except ValueError:
            flash("Невірний формат числових полів (ціна та площа повинні бути числами)", "danger")
            return render_template('property_form.html', offer=offer, photos_serialized=photos_serialized)
        
        
        try:
            data = {
                "address": address,
                "district": district,
                "city": city,
                "price": price_val,
                "area": area_val,
                "description": description,
                "repair": repair,
            }
            offer = OffersService.update_offer(offer, data)
        
            # Update recommended businesses: delete old, add new
            RecommendedBusiness.query.filter_by(listing_id=offer.id).delete()
            recommended_types = request.form.getlist('recommended_types')
            for type_id in recommended_types:
                try:
                    type_id_int = int(type_id)
                    rec = RecommendedBusiness(listing_id=offer.id, type_id=type_id_int)
                    db.session.add(rec)
                except ValueError:
                    continue


            # Handle photo deletions
            photos_to_delete = request.form.getlist('delete_photos')
            print(f"Photos to delete: {photos_to_delete}")  # Debug log
            if photos_to_delete !=['']:
                for photo_id in photos_to_delete:
                    photo = OfferPhoto.query.get(int(photo_id))
                    if photo and photo.offer_id == offer.id:
                        file_path = os.path.join(current_app.config["UPLOAD_FOLDER"], photo.photo_url.replace('photos/', ''))
                        if os.path.exists(file_path):
                            os.remove(file_path)
                        db.session.delete(photo)


            # Handle new primary photo
            new_primary_id = request.form.get('primary_photo')
            print(f"New primary photo ID: {new_primary_id}")  # Debug log
            if new_primary_id:
                # Reset all to non-primary
                OfferPhoto.query.filter_by(offer_id=offer.id).update({"is_primary": False})
                # Set new primary
                primary_photo = OfferPhoto.query.get(int(new_primary_id))
                if primary_photo and primary_photo.offer_id == offer.id:
                    primary_photo.is_primary = True

            # Handle new photo uploads
            files = request.files.getlist("photos")
            for idx, file in enumerate(files):
                if not file or file.filename == "":
                    continue
                if not allowed_file(file.filename):
                    continue

                filename = unique_filename(file.filename)
                upload_folder = current_app.config["UPLOAD_FOLDER"]
                file_path = os.path.join(upload_folder, filename)
                file.save(file_path)

                relative_path = os.path.join("photos", filename).replace("\\", "/")

                # If no primary set yet, make first new photo primary
                is_primary = (idx == 0 and not OfferPhoto.query.filter_by(offer_id=offer.id, is_primary=True).first())

                photo = OfferPhoto(
                    offer_id=offer.id,
                    photo_url=relative_path,
                    is_primary=is_primary
                )
                db.session.add(photo)
            db.session.commit()

            flash("Оголошення успішно оновлено", "success")
            return redirect(url_for("test.property_detail", offer_id=offer.id))
        except ValueError:
            flash("Не вдалося оновити оголошення", "danger")


    return render_template('property_form.html', offer=offer, photos_serialized=photos_serialized, business_types=business_types_serialized, current_recommended=current_recommended)

       
@test.route('/my-properties', methods=['GET'])
@login_required
@roles_required(User.ROLE_LANDLORD)
def my_properties():
    offers = OffersService.get_offers_by_owner(current_user.id)
    serialized = OffersService.serialize_multiple(offers)
    total = len(offers)
    approved = sum(1 for o in offers if getattr(o, 'approved', False))
    pending = total - approved
    return render_template('my_properties.html', offers=serialized, total=total, approved=approved, pending=pending)





    


