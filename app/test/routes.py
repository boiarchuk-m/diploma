from app import db
from app.test import test
from app.models.comm_leasing import CommLeasing
from app.models.business_type import Business_type
from app.models.nearby_business import NearbyBusiness
import json
from flask import Response
from flask import render_template, request, jsonify




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
    return render_template("onboarding.html",
                           categories = categories_list,
                           districts = districts)


@test.route("/onboarding/offers", methods=["POST"])
def onboarding_submit():
    data = request.get_json()
    print("Received onboarding data:", data)
    return jsonify({"status": "ok", "received": data})


@test.route("/test")
def algorytm():
    business_map = {
        "Кав’ярня/кафе": "cafes",
        "Ресторан": "restaurants",
        "Бар/Паб": "bars_pubs",
        "Магазин продуктів": "grocery_stores",
        "Магазин одягу/взуття": "clothing_shops",
        "Аптека": "pharmacies",
        "Салон краси": "beauty_salons",
        "Магазин квітів": "flower_shops",
        "Зоомагазин": "pet_shops",
        "Ательє/ремонт одягу": "ateliers",
        "Ремонт техніки/сервісний центр": "repair_services",
        "Фітнес-зал/студія": "gyms"
    }

    user_choice = {
        "business_type": "Кав’ярня/кафе",
        #"business_type": "Інше",
        "area":  {'min': 40, 'max': 70},
        "preferred_districts": ["Шевченківський", "Печерський"]
    }


    def get_weights(user_choice):
        weights =None
        business = user_choice['business_type']
        if business== "Інше":
            weights = {
                'area': 0.3,
                'price': 0.2,
                'stops': 0.2,
                'competitors': 0,
                'otherbiz': 0.3
            }
        else:
            business_type = (db.session.query(Business_type).
                             filter(Business_type.business_type == business).
                             first())
            weights = {
                    'area': business_type.w_area,
                    'price': business_type.w_price,
                    'stops': business_type.w_stops,
                    'competitors': business_type.w_competitors,
                    'otherbiz': business_type.w_otherbiz
                }


        return weights

    def get_offers(user_choice):
        preferred_districts = user_choice['preferred_districts']
        offers = (db.session.query(CommLeasing).
                  filter(CommLeasing.district.in_(preferred_districts)).
                  all())
        if offers:
            return {"note": "Filtered results", "data": offers}
        else:
            offers = (db.session.query(CommLeasing).
                      all())
            return {"note": "No results for filtered values", "data": offers}

    def desirability_area(x, low, high):
        if low is None or high is None:
            return 1.0
        tol = (high - low) / 3
        if low <= x <= high:
            return 1.0
        elif low - tol < x < low:
            return (x - (low - tol)) / tol
        elif high < x < high + tol:
            return ((high + tol) - x) / tol
        else:
            return 0.0

    def get_matrix(offers, user_choise):
        area_min = user_choise['area']['min']
        area_max = user_choise['area']['max']
        business_type = business_map[user_choice['business_type']]
        criteria_rows = []
        for o in offers:
            env = db.session.query(NearbyBusiness).filter_by(offer_id=o.id).first()
            if not env:
                continue
            area_val =o.area
            area= desirability_area(area_val, area_min, area_max)
            competitors = getattr(env, business_type)
            otherbiz = sum([
                getattr(env, col) for col in business_map.values()
                if col != business_type
            ])
            stops = env.stops

            criteria_rows.append({
                'Alternative': o.id,
                'Area': area,
                'Price': o.price,
                'Stops': stops,
                'Competitors': competitors,
                'OtherBiz': otherbiz
            })

        return jsonify(criteria_rows)



    weights = get_weights(user_choice)
    offers = get_offers(user_choice)
    matrix = get_matrix(offers['data'], user_choice)

    return matrix

