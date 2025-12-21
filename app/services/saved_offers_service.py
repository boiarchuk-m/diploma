from app.models.saved_offers import SavedOffer
from app import db

class SavedOffersService:

    @staticmethod
    def get_saved_offers_by_user(user_id: int) -> list[SavedOffer]:
        """Повертає список збережених оголошень користувача."""
        return SavedOffer.query.filter_by(user_id=user_id).all()
    
    @staticmethod
    def add_saved_offer(user_id: int, offer_id: int) -> SavedOffer:
        """Додає оголошення до збережених для користувача."""
        saved_offer = SavedOffer(user_id=user_id, offer_id=offer_id)
        db.session.add(saved_offer)
        db.session.commit()
        return saved_offer
    
    @staticmethod
    def remove_saved_offer(user_id: int, offer_id: int) -> None:
        """Видаляє оголошення зі збережених для користувача."""
        saved_offer = SavedOffer.query.filter_by(user_id=user_id, offer_id=offer_id).first()
        if saved_offer:
            db.session.delete(saved_offer)
            db.session.commit()
    

