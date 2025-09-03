from app import db
from app.test import test
from app.models.comm_leasing import CommLeasing
from app.models.businesses import Businesses
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
    businesses = Businesses.query.with_entities(Businesses.business,
                                          Businesses.squaremin,
                                          Businesses.squaremax).all()
    categories_list = [
        {
            "business": c.business,
            "squaremin": c.squaremin,
            "squaremax": c.squaremax
        }
        for c in businesses
    ]

    unique_districts = db.session.query(CommLeasing.district).distinct().all()
    districts = [d[0] for d in unique_districts]
    return render_template("onboarding.html",
                           categories = categories_list,
                           districts = districts)


@test.route("/api/onboarding", methods=["POST"])
def onboarding_submit():
    data = request.get_json()
    print("Received onboarding data:", data)
    # тут зберігаєш в БД або обробляєш
    return jsonify({"status": "ok", "received": data})