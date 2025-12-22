from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user

from app.services.ranking_service import RankingService
import json
from flask import session
from app.services.offers_service import OffersService
from app.utils.decorators import roles_required
from app.models.user import User

onboarding_bp = Blueprint("onboarding", __name__)


@onboarding_bp.route('/onboarding')
def onboarding():
    """Форма онбордингу - вибір параметрів для ранжування."""
    data = OffersService.get_initial_data()
    return render_template("onboarding.html",   
                           categories = data["categories"],
                           districts = data["districts"],
                           cities = data["cities"]
                           )


@onboarding_bp.route("/onboarding/offers", methods=["POST"])
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

    return redirect(url_for('onboarding.list_ranked_properties'))


@onboarding_bp.route('/properties/ranked', methods=['GET'])
def list_ranked_properties():

    user_choice = session.get("user_choice", {})

    #offer_ids, ranking_results = OnboardingService.run_ranking(user_choice)
    results = RankingService(user_choice).run()

    offers_for_view = OffersService.build_ranked_offers(results)

    #offers_for_view = OnboardingService.build_ranked_offers(offer_ids, ranking_results)

    return render_template('properties_onb.html', offers=offers_for_view)

