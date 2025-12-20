from flask  import url_for
from app import db
from app.models.comm_leasing import CommLeasing
from app.models.offer_photo import OfferPhoto
from app.models.recommended_business import RecommendedBusiness
from app.models.business_type import Business_type
import re
import math
from typing import List


class OffersService:
    """Service to fetch and serialize commercial leasing offers."""

    @staticmethod
    def get_by_id(property_id: int):
        """Повертає оголошення за ID або None."""
        return CommLeasing.query.get(property_id)

    @staticmethod
    def get_multiple(ids: list[int]):
        """Повертає словник об'єктів за списком ID."""
        offers = CommLeasing.query.filter(CommLeasing.id.in_(ids)).all()
        return {o.id: o for o in offers}

    @staticmethod
    def get_all():
        """Повертає всі оголошення."""
        return CommLeasing.query.all()

    @staticmethod
    def serialize_offer(offer: CommLeasing):
        """Серіалізує оголошення у словник з фото."""
        data = offer.serialize()
        photos = OfferPhoto.query.filter_by(offer_id=offer.id).all()
        data["photos"] = [
            url_for("static", filename=p.photo_url.replace("\\", "/").lstrip("/"))
            for p in photos
        ]

        businesses  = RecommendedBusiness.query.filter_by(listing_id=offer.id).all()

        business_types = [rb.business_type.business_type for rb in businesses]
        data["recommended_types"] = business_types if business_types else []
        owner = offer.owner
        if owner:
            phone = owner.phone_number or ""
            phone_clean = re.sub(r"\D+", "", phone) if phone else ""

            data["owner"] = {
                "id": owner.id,
                "first_name": owner.first_name,
                "last_name": owner.last_name,
                "email": owner.email,
                "phone": phone,
                "phone_clean": phone_clean,
                "company_name": owner.company_name,
                "contact_telegram": owner.contact_telegram,
                "contact_viber": owner.contact_viber,
                "contact_whatsapp": owner.contact_whatsapp,
            }
        else:
            data["owner"] = None
        return data
    
    @staticmethod
    def serialize_multiple(offers: list[CommLeasing]) -> list[dict]:
        return [OffersService.serialize_offer(o) for o in offers]
    
    @staticmethod
    def attach_ranking_data(offer_map: dict, ranking_list: list[dict]):
        """
        Об'єднує ранги з даними оголошень.
        ranking_list = [{id: X, rank: Y, score: Z}, ...]
        """
        result = []

        for r in ranking_list:
            offer = offer_map.get(r["id"])
            if not offer:
                continue

            full = OffersService.serialize_offer(offer)
            full["rank"] = r["rank"]
            full["score"] = r.get("score")

            full["competitors_count"] = r.get("competitors_count", 0)
            full["other_businesses_count"] = r.get("other_businesses_count", 0)

            result.append(full)

        # сортування за рангом
        return sorted(result, key=lambda x: x["rank"])
    
    @staticmethod
    def filter_offers(offers: list[dict], filters: dict) -> list[dict]:
        """
        Фільтрує готовий список даних:
        - як повний список, так і ранжований.
        - НЕ викликає БД
        """

        result = offers
        print(offers)

        if "max_price" in filters and filters["max_price"]:
            result = [o for o in result if o.get("price") <= filters["max_price"]]

        if "min_price" in filters and filters["min_price"]:
            result = [o for o in result if o.get("price") >= filters["min_price"]]

        if "min_area" in filters and filters["min_area"]:
            result = [o for o in result if o.get("area") >= filters["min_area"]]

        if "max_area" in filters and filters["max_area"]:
            result = [o for o in result if o.get("area") <= filters["max_area"]]

        if "districts" in filters and filters["districts"]:
            result = [o for o in result if o.get("district") in filters["districts"]]

        if "repair_types" in filters and filters["repair_types"]:
            print("Filtering by repair types:", filters["repair_types"])
            result = [o for o in result if o.get("repair") in filters["repair_types"]]

        # сортування
        sort_type = filters.get("sort")
        if sort_type == "price_asc":
            result = sorted(result, key=lambda x: x["price"])
        elif sort_type == "price_desc":
            result = sorted(result, key=lambda x: x["price"], reverse=True)
        elif sort_type == "rank":
            result = sorted(result, key=lambda x: x.get("rank", 999))
        elif sort_type == "area":
            result = sorted(result, key=lambda x: x["area"])

        return result
    


    # CRUD operations 

    @staticmethod
    def create_offer(data: dict, owner_id: int |None = None) -> CommLeasing:
        """Створює нове оголошення."""
        offer = CommLeasing(
            address=data["address"],
            district=data["district"],
            price=data["price"],
            area=data["area"],
            description=data.get("description"),
            repair=data.get("repair"),
            city=data.get("city"),
            recommended_for=data.get("recommended_for"),
            stops_num=data.get("stops_num"),
            owner_id=owner_id
        )
        db.session.add(offer)
        db.session.commit()
        return offer
    
    @staticmethod
    def update_offer(offer: CommLeasing, data: dict) -> CommLeasing:
        """Оновлює існуюче оголошення."""
        fields = [
            "address", "district", "city", "price", "area",
            "description", "repair", "recommended_for", "stops_num"
        ]
        for field in fields:
            if field in data and data[field] is not None:
                setattr(offer, field, data[field])
        db.session.commit()
        return offer
    
    @staticmethod
    def delete_offer(offer: CommLeasing) -> None:
        """Видаляє оголошення."""
        db.session.delete(offer)
        db.session.commit()

    @staticmethod
    def approve_offer(offer: CommLeasing) -> None:
        """Затверджує оголошення."""
        offer.approved = Trueп
        db.session.commit()
    
    @staticmethod
    def get_offers_by_owner(owner_id: int) -> list[CommLeasing]:
        """Повертає всі оголошення певного власника."""
        return CommLeasing.query.filter_by(owner_id=owner_id).all()

    @staticmethod
    def get_pending_offers() -> list[CommLeasing]:
        """Повертає всі не затверджені оголошення."""
        return CommLeasing.query.filter_by(approved=False).all()
    
    @staticmethod
    def count_offers() -> int:
        """Повертає загальну кількість оголошень."""
        return CommLeasing.query.count()
    
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
    def build_ranked_offers(ranked_items: List[dict]) -> List[dict]:
        """Об'єднує результати ранжування з детальною інформацією про оголошення з БД.
        
        :param ranked_items: Список словників, який повернув метод run() вашого сервісу.
                            Приклад: [{'id': 1, 'rank': 1, 'score': 0.8, ...}, ...]"""

        # 1. Fallback: Якщо ранжування нічого не повернуло (порожній список)
        # Повертаємо просто всі оголошення без ранжування (як було у вашому старому коді)
        if not ranked_items:
            offers = OffersService.get_all()
            return OffersService.serialize_multiple(offers)
        
        # 2. Витягуємо список ID для запиту в базу даних
        # Це потрібно, щоб зробити один ефективний запит замість N запитів у циклі
        offer_ids = [item['id'] for item in ranked_items]

        # 3. Отримуємо "важкі" об'єкти з БД (SQLAlchemy objects)
        # Повертає словник {id: OfferObject}
        offers_map = OffersService.get_multiple(offer_ids)

        offers_for_view: List[dict] = []

        # 4. Проходимо по ранжованому списку (щоб зберегти порядок сортування TOPSIS)
        for meta_data in ranked_items:
            oid = meta_data['id']
            offer_db = offers_map.get(oid)
            
            # Якщо з якоїсь причини об'єкта немає в базі (видалений), пропускаємо
            if not offer_db:
                continue

            # Серіалізуємо дані з БД (Title, Price, Area, Photos)
            serialized = OffersService.serialize_offer(offer_db)

            # 5. MERGE: Додаємо аналітичні дані, які ми порахували в run()
            # Використовуємо .update() для чистоти коду
            serialized.update({
                "rank": meta_data.get("rank"),
                "score": meta_data.get("score"),
                "competitors_count": meta_data.get("competitors_count"),
                "other_businesses_count": meta_data.get("other_businesses_count")
            })

            offers_for_view.append(serialized)
    
        # 6. Фінальне сортування (про всяк випадок, хоча ranked_items вже має бути відсортованим)
        # Використовуємо float('inf') щоб елементи без рангу (якщо такі будуть) йшли в кінець
        offers_for_view.sort(key=lambda x: x.get("rank") if x.get("rank") is not None else float('inf'))

        return offers_for_view


    
