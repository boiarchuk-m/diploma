import math
import numpy as np
from flask import url_for
from app.services.decision_methods.topsis import topsis
from app import db
from app.models.comm_leasing import CommLeasing
from app.models.business_type import Business_type
from app.models.num_businesses import NumBusinesses
from app.models.offer_photo import OfferPhoto


class RankingService:

    criteria_cols = ["area", "price", "stops", "competitors", "otherbiz"]
    cost_cols = ["price", "competitors"] 

    def __init__(self, user_choice):
        self.business_type = user_choice.get("business_type")
        self.business_type_id = user_choice.get("business_type_id")

        area = user_choice.get("area", {})
        self.area_min = area.get("min")
        self.area_max = area.get("max")

        self.districts = user_choice.get("preferred_districts", [])
        self.city = user_choice.get("city")

        self.offers = []
        self.matrix_rows = []
        self.weights = {}


    def get_weights(self):

        if self.business_type_id is None:
            return {
                'area': 0.3,
                'price': 0.2,
                'stops': 0.2,
                'competitors': 0,
                'otherbiz': 0.3
            }

        bt = Business_type.query.filter_by(id=self.business_type_id).first()
        return {
            "area": bt.w_area,
            "price": bt.w_price,
            "stops": bt.w_stops,
            "competitors": bt.w_competitors,
            "otherbiz": bt.w_otherbiz
        }
    
    def get_offers(self):
        q = CommLeasing.query
        
        if self.districts:
            q = q.filter(CommLeasing.district.in_(self.districts))
            return q.all()

        if self.city:
            offers = CommLeasing.query.filter_by(city=self.city).all()
            if offers:
                return offers

        return CommLeasing.query.all()
    
    def desirability_area(self, x, percentage=0.3):
        if self.area_min is None or self.area_max is None:
            return 1.0

        low_lim = self.area_min * (1 - percentage)
        high_lim = self.area_max * (1 + percentage)

        if self.area_min <= x <= self.area_max:
            return 1.0
        if low_lim < x < self.area_min:
            return (x - low_lim) / (self.area_min - low_lim)
        elif self.area_max < x < high_lim:
            return (high_lim - x) / (high_lim - self.area_max)
        return 0.0
    
    def build_matrix(self):
        rows = []

        for o in self.offers:
            comp = (
                NumBusinesses.query
                .filter_by(offer_id=o.id, business_type_id=self.business_type_id)
                .with_entities(NumBusinesses.number)
                .scalar()
                or 0
            )
            otherbiz = (
                NumBusinesses.query
                .with_entities(db.func.sum(NumBusinesses.number))
                .filter(NumBusinesses.offer_id == o.id,
                        NumBusinesses.business_type_id != self.business_type_id)
                .scalar()
                or 0
            )
            rows.append({
                "alternative": o.id,
                "area": self.desirability_area(o.area),
                "price": o.price,
                "stops": o.stops_num,
                "competitors": comp,
                "otherbiz": otherbiz
            })
        return rows
    
    def run_topsis(self):
        
        matrix = [[row[c] for c in self.criteria_cols] for row in self.matrix_rows]
        weights_vector = [self.weights[c] for c in self.criteria_cols]

        cost_idx = [
            self.criteria_cols.index(col)
            for col in self.cost_cols
        ]

        scores, ranks = topsis(
            matrix,
            weights_vector,
            cost_cols=cost_idx
        )

        # attach scores/ranks back to rows
        for row, s, r in zip(self.matrix_rows, scores, ranks):
            row["Score"] = float(s)
            row["Rank"] = int(r)

        return self.matrix_rows


    def prepare_output(self):
        output = []
        offer_map = {o.id: o for o in self.offers}

        for row in self.matrix_rows:
            offer = offer_map[row["alternative"]]
            item = offer.serialize()
            item["Rank"] = row["Rank"]

            photos = OfferPhoto.query.filter_by(
                offer_id=offer.id,
                is_primary=True
            ).all()

            item["photos"] = [
                url_for("static", filename=p.photo_url.replace("\\", "/").lstrip("/"))
                for p in photos
            ]

            output.append(item)

        output.sort(key=lambda x: x["Rank"])
        return output
    
    def run(self):
        self.weights = self.get_weights()
        self.offers = self.get_offers()
        self.matrix_rows = self.build_matrix()
        self.matrix_rows = self.run_topsis()
        print("Final matrix rows with scores and ranks:", self.matrix_rows)
        return self.prepare_output()




    



