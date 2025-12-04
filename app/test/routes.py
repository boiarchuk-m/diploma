from app import db
from app.test import test
from app.models.comm_leasing import CommLeasing
from app.models.business_type import Business_type
from app.models.nearby_business import NearbyBusiness
from app.models.num_businesses import NumBusinesses
from app.models.offer_photo import OfferPhoto
from app.services.auth_service import AuthService
from app.models.user import User
from flask_login import login_user, logout_user, login_required

import json
from flask import Response, flash, redirect
from flask import render_template, request, jsonify, url_for
import math
from app.services.ranking_service import RankingService
from app.services.offers_service import OffersService



@test.route('/')
def index():
    res = CommLeasing.query.limit(10).all()
    data = [p.serialize() for p in res]
    #return jsonify(data)
    #return Response(
    #    json.dumps(data, ensure_ascii=False),
    #    mimetype="application/json"
    #)
    return render_template ('main.html')

@test.route('/onboarding')
def onboarding():
    businesses = Business_type.query.with_entities(Business_type.id,
                                          Business_type.business_type,
                                          Business_type.min_area,
                                          Business_type.max_area).all()
    categories_list = [
        {
            "id": c.id,
            "business_type": c.business_type,
            "min_area": c.min_area,
            "max_area": c.max_area
        }
        for c in businesses
    ]

    unique_districts = db.session.query(CommLeasing.district).distinct().all()
    districts = [d[0] for d in unique_districts]
    unique_cities = db.session.query(CommLeasing.city).distinct().all()
    cities = [c[0] for c in unique_cities]
    return render_template("onboarding.html",
                           categories = categories_list,
                           districts = districts,
                           cities = cities
                           )


@test.route("/onboarding/offers", methods=["POST", "GET"])
def onboarding_submit():
    data = request.get_json(silent=True)
    print("Received onboarding data:", data)
    if not data and request.form.get('payload'):
        data = json.loads(request.form['payload'])
    data = data or {}
    print("Processed onboarding data:", data)

    # normalize incoming payload
    user_choice = {
        "business_type": data.get("business_type"),
        "business_type_id": data.get("business_type_id"),
        "area": {"min": data.get("area", {}).get("min"),
                 "max": data.get("area", {}).get("max")},
        "preferred_districts": data.get("districts", []),
        "city": data.get("city")
    }

    #results = run_algorithm(user_choice)

    service = RankingService(user_choice)
    results = service.run()

    ids = [r["id"] for r in results]
    offer_map = OffersService.get_multiple(ids)

    offers_with_ranks = OffersService.attach_ranking_data(offer_map, results)

    #return  jsonify(results)

    return render_template('properties_onb.html', offers=offers_with_ranks)


@test.route('/results_page')
def results_page():
    return render_template('offers.html')


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
            return redirect(url_for("users.edit_landlord_profile"))
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



    


