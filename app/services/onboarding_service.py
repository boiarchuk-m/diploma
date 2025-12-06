from app import db
from app.models.business_type import Business_type
from app.models.comm_leasing import CommLeasing
from app.services.ranking_service import RankingService
from app.services.offers_service import OffersService
from typing import List, Dict, Any
import math


class OnboardingService:

    @staticmethod
    def get_initial_data():
        """Дані для відображення форми онбордингу (списки бізнесів, міст, районів)."""
        businesses = (
            Business_type.query
            .with_entities(
                Business_type.id,
                Business_type.business_type,
                Business_type.min_area,
                Business_type.max_area
            )
            .all()
        )
        categories_list = [
            {
                "id": b.id,
                "business_type": b.business_type,
                "min_area": b.min_area,
                "max_area": b.max_area
            }
            for b in businesses
        ]

        cities = db.session.query(CommLeasing.city).distinct().all()
        districts = db.session.query(CommLeasing.district).distinct().all()
        unique_districts = db.session.query(CommLeasing.district).distinct().all()
        districts = [d[0] for d in unique_districts]
        unique_cities = db.session.query(CommLeasing.city).distinct().all()
        cities = [c[0] for c in unique_cities]
        
        return {
            "categories": categories_list,
            "districts": districts,
            "cities": cities
        }

    @staticmethod
    def normalize_user_choice(raw: dict) -> dict:
        """Нормалізує вибір користувача з форми онбордингу."""
        raw = raw or {}
        
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


        return user_choice
    

    @staticmethod
    def run_ranking(user_choice: dict) -> Dict[str, Any]:
        """Запускає ранжування оголошень на основі вибору користувача."""
        service = RankingService(user_choice)
        service.run()

        offer_ids = [row["alternative"] for row in service.matrix_rows]

        # мета-дані ранжування (для зберігання в session)
        ranking_results = {
            str(row["alternative"]): {
                "rank": row.get("Rank"),
                "competitors_count": row.get("competitors"),
                "other_businesses_count": row.get("otherbiz"),
                "score": row.get("Score")
            }
            for row in service.matrix_rows
        }

        return offer_ids, ranking_results
        

    @staticmethod
    def build_ranked_offers(offer_ids: List[int],
                            ranking_results: Dict[str, dict]) -> List[dict]:
        """Повертає ранжований список оголошень на основі вибору користувача."""

        if not offer_ids:
            # fallback: show all offers without ranking
            offers = OffersService.get_all()
            return OffersService.serialize_multiple(offers)
        
        # Get offers from DB
        offers_map = OffersService.get_multiple(offer_ids)  # {id: CommLeasing}

        offers_for_view: List[dict] = []

        for oid in offer_ids:
            offer = offers_map.get(oid)
            if not offer:
                continue

            serialized = OffersService.serialize_offer(offer)

            extra = ranking_results.get(str(oid))

            if extra:
                serialized["rank"] = extra.get("rank")
                serialized["competitors_count"] = extra.get("competitors_count")
                serialized["other_businesses_count"] = extra.get("other_businesses_count")
                serialized["score"] = extra.get("score")

            offers_for_view.append(serialized)
        
        offers_for_view.sort(key=lambda x: x.get("rank", math.inf))


        return offers_for_view