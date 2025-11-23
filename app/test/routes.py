from app import db
from app.test import test
from app.models.comm_leasing import CommLeasing
from app.models.business_type import Business_type
from app.models.nearby_business import NearbyBusiness
from app.models.num_businesses import NumBusinesses
from app.models.offer_photo import OfferPhoto
import json
from flask import Response
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

    #return  jsonify(results)

    return render_template('offers.html', offers=results)


@test.route('/results_page')
def results_page():
    return render_template('offers.html')


@test.route('/properties', methods=['GET'])
def list_properties():
    offers = OffersService.get_all()
    offers_serialized = OffersService.serialize_multiple(offers)

    filters = {
        "min_price": request.args.get("min_price", type=int),
        "max_price": request.args.get("max_price", type=int),
        "min_area": request.args.get("min_area", type=int),
        "max_area": request.args.get("max_area", type=int),
        "districts": request.args.getlist("districts"),
        "repair_types": request.args.getlist("repair_types"),
        "sort": request.args.get("sort")
    }

    filtered = OffersService.filter_offers(offers_serialized, filters)
    return render_template('properties.html', offers=filtered, filters=filters)

@test.route("/properties/filter", methods=["POST"])
def filter_properties_api():
    """
    Приймає фільтри через JSON (AJAX)
    і повертає JSON відповідь.
    """

    filters = request.get_json() or {}

    offers = OffersService.get_all()
    serialized = OffersService.serialize_multiple(offers)

    filtered = OffersService.filter_offers(serialized, filters)

    return jsonify(filtered)




    


