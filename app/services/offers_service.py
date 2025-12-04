from flask  import url_for
from app import db
from app.models.comm_leasing import CommLeasing
from app.models.offer_photo import OfferPhoto


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
    def create_offer(data: dict) -> CommLeasing:
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
            stops_num=data.get("stops_num")
        )
        db.session.add(offer)
        db.session.commit()
        return offer
    
    @staticmethod
    def update_offer(offer: CommLeasing, data: dict) -> CommLeasing:
        """Оновлює існуюче оголошення."""
        for key, value in data.items():
            setattr(offer, key, value)
        db.session.commit()
        return offer
    
    @staticmethod
    def delete_offer(offer: CommLeasing) -> None:
        """Видаляє оголошення."""
        db.session.delete(offer)
        db.session.commit()


    
