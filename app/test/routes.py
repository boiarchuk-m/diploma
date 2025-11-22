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




def run_algorithm(user_choice):
    print("User choice at start of run_algorithm:", user_choice)
     # resolve business type name if id provided
    #if user_choice.get('business_type_id') and not user_choice.get('business_type'):
    #    bt = Business_type.query.get(user_choice['business_type_id'])
    #    user_choice['business_type'] = bt.business_type if bt else "Інше"


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

   # user_choice = {
    #    "business_type": "Кав’ярня/кафе",
    #    #"business_type": "Інше",
    #    "area":  {'min': 40, 'max': 70},
    #    "preferred_districts": ["Шевченківський", "Печерський"]
    #}


    def get_weights(user_choice):
        print("User choice in get_weights:", user_choice)
        business = user_choice.get('business_type')
        print("business_type", business)
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
        q= db.session.query(CommLeasing)
        preferred_districts = user_choice.get('preferred_districts') or []
        if preferred_districts:
            q=q.filter(CommLeasing.district.in_(preferred_districts))
        offers = q.all()
        if offers:
            return {"note": "Filtered results", "data": offers}
        
        if user_choice.get('city'):
            offers = db.session.query(CommLeasing).filter(CommLeasing.city == user_choice['city']).all()
            if offers:
                return {"note": "City filtered results", "data": offers}
        # fallback: all offers
        offers = db.session.query(CommLeasing).all()
        return {"note": "All results", "data": offers}

    def desirability_area(x, low, high, persentage=0.3):
        if low is None or high is None:
            return 1.0
        low_lim = low * (1 - persentage)
        high_lim = high * (1 + persentage)
        if low <= x <= high:
            return 1.0
        elif low_lim < x < low:
            return (x - low_lim) / (low - low_lim)
        elif high < x < high_lim:
            return (high_lim - x) / (high_lim - high)
        else:
            return 0.0

    def get_matrix(offers, user_choise):
        area_min = user_choise.get('area', {}).get('min')
        area_max = user_choise.get('area', {}).get('max')
        business_type = business_map.get(user_choice.get('business_type'))
        business_type_id = user_choice.get('business_type_id')
        criteria_rows = []
        for o in offers:
            area_val =o.area
            area= desirability_area(area_val, area_min, area_max)
            stops = o.stops_num
            comp =  db.session.query(NumBusinesses.number).filter_by(offer_id=o.id, business_type_id=business_type_id).first()
            competitors = comp.number if comp else 0
            otherbiz = db.session.query(db.func.sum(NumBusinesses.number)).filter(NumBusinesses.offer_id == o.id,
            NumBusinesses.business_type_id != business_type_id).scalar()        

            criteria_rows.append({
                'alternative': o.id,
                'area': area,
                'price': o.price,
                'stops': stops,
                'competitors': competitors,
                'otherbiz': otherbiz,
            })
        #print("Criteria Rows:", criteria_rows)
        return criteria_rows


    def calculations(criteria_rows, weights):
        cols = ['area', 'price', 'stops', 'competitors', 'otherbiz']
        criteria = {
                'area': 'benefit',
                'price': 'cost',
                'stops': 'benefit',
                'competitors': 'cost',
                'otherbiz': 'benefit'
            }

        for row in criteria_rows:
            for col, t in criteria.items():
                if t == 'cost':
                    row[col] = 1 / (row[col] + 1e-12) # avoid division by zero

        # normalizing
        norm_factors = {}
        for col in cols:
            norm_factors[col] = math.sqrt(sum(row[col] ** 2 for row in criteria_rows))
        for row in criteria_rows:
            for col in cols:
                row[col] = row[col] / norm_factors[col] if norm_factors[col] != 0 else 0

        for row in criteria_rows:
            for col in cols:
                row[col] *= weights[col]

        # Ідеальний та антиідеальний розв’язки
        ideal = {col: max(row[col] for row in criteria_rows) for col in cols}
        antei = {col: min(row[col] for row in criteria_rows) for col in cols}

        # Відстані до ідеалу та антиідеалу
        for row in criteria_rows:
            d_plus = math.sqrt(sum((row[col] - ideal[col]) ** 2 for col in cols))
            d_minus = math.sqrt(sum((row[col] - antei[col]) ** 2 for col in cols))
            row['Score'] = d_minus / (d_plus + d_minus) if (d_plus + d_minus) != 0 else 0

        # Ранжування
        sorted_scores = sorted([row['Score'] for row in criteria_rows], reverse=True)
        for row in criteria_rows:
            row['Rank'] = sorted_scores.index(row['Score']) + 1

        return criteria_rows


    def get_results(results, offers):
        final_output=[]

        offers_map = {o.id: o for o in offers}

        for r in results:
            offer = offers_map.get(r['alternative'])
            if not offer:
                continue
            data = offer.serialize()
            data['Rank'] = r['Rank']

            photos =(OfferPhoto.query.
                     filter(OfferPhoto.offer_id == offer.id)
                     .filter(OfferPhoto.is_primary == True)
                     .all())
            
            photo_urls = [p.photo_url for p in photos]
            urls=[]
            for p in photo_urls:
                path = p.replace('\\', '/').lstrip('/')
                urls.append(url_for('static', filename=path))
            data['photos'] = urls
                
            final_output.append(data)

          # sort by Rank ascending (1 = best)
        final_output.sort(key=lambda x: x.get('Rank', float('inf')))


        return final_output




    weights = get_weights(user_choice)
    print("Weights:", weights)
    offers = get_offers(user_choice)
    matrix = get_matrix(offers['data'], user_choice)
    print("Matrix:", matrix)
    res = calculations(matrix, weights)
    print("Calculations result:", res)
    final_res = get_results(res, offers['data'])

    return final_res

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

    return  jsonify(results)

    #return render_template('offers.html', offers=results)



@test.route("/test")
def algorytm():
    # default/hardcoded example for testing
    default_choice = {
        "business_type": "Кав’ярня/кафе",
        "area": {'min': 40, 'max': 70},
        "preferred_districts": ["Шевченківський", "Печерський"]
    }
    results = run_algorithm(default_choice)
    return jsonify(results)

@test.route('/results_page')
def results_page():
    return render_template('offers.html')

