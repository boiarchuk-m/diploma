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
        q = CommLeasing.query.filter_by(approved=True)
        
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
                "otherbiz": otherbiz,

                "competitors_count": comp,
                "other_businesses_count": otherbiz
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
        
        offer_ids = [row["alternative"] for row in self.matrix_rows]

        # мета-дані ранжування (для зберігання в session)
        ranking_results = {
            str(row["alternative"]): {
                "rank": row.get("Rank"),
                "competitors_count": row.get("competitors"),
                "other_businesses_count": row.get("otherbiz"),
                "score": row.get("Score")
            }
            for row in self.matrix_rows
        }
        return offer_ids, ranking_results
    
    def run(self):
        self.weights = self.get_weights()
        self.offers = self.get_offers()
        self.matrix_rows = self.build_matrix()
        self.matrix_rows = self.run_topsis()
        

        results = []
        for row in self.matrix_rows:
            results.append({
                # Основні ідентифікатори та оцінки
                "id": row["alternative"],
                "rank": row.get("Rank"),
                "score": row.get("Score"),
                
                # Аналітичні дані (які ми порахували динамічно)
                "competitors_count": row.get("competitors") or row.get("competitors_count", 0),
                "other_businesses_count": row.get("otherbiz") or row.get("other_businesses_count", 0)
            })

        # 3. Сортування результатів (від 1-го місця до останнього)
        results.sort(key=lambda x: x["rank"] if x["rank"] is not None else float('inf'))

        #return self.prepare_output()
        return results




    



