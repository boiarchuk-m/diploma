from __future__ import annotations

from typing import Optional, List
from app import db
from app.models.comm_leasing import CommLeasing


class AdminService:
    """Адмін-логіка: модерація оголошень (pending, approve, comment, delete)."""

    @staticmethod
    def get_pending_offers(limit: int = 200) -> List[CommLeasing]:
        """Оголошення, які ще не підтверджені."""
        return (
            CommLeasing.query
            .filter(CommLeasing.approved.is_(False))
            .filter(CommLeasing.comment.is_(None))
            .order_by(CommLeasing.id.desc())
            .limit(limit)
            .all()
        )
    
    @staticmethod
    def get_offer(offer_id: int) -> Optional[CommLeasing]:
        return CommLeasing.query.get(offer_id)
    
    @staticmethod
    def add_comment(offer_id: int, comment: str) -> CommLeasing:
        """Додає/оновлює коментар адміна."""
        offer = CommLeasing.query.get_or_404(offer_id)
        offer.comment = (comment or "").strip()
        db.session.commit()
        return offer
    
    @staticmethod
    def approve_offer(offer_id: int, comment: Optional[str] = None) -> CommLeasing:
        """Підтверджує оголошення."""
        offer = CommLeasing.query.get_or_404(offer_id)
        offer.approved = True

        if comment is not None:
            offer.comment = None

        db.session.commit()
        return offer
    
    


    