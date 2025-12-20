from app import db



class OfferPhoto(db.Model):
    __tablename__ = 'offer_photos'

    id = db.Column(db.Integer, primary_key=True)
    offer_id = db.Column(db.Integer, db.ForeignKey('commercial_listings.id'), nullable=False)
    photo_url = db.Column(db.String(255), nullable=False)  
    is_primary = db.Column(db.Boolean, default=False)

    com_leasing = db.relationship('CommLeasing', backref=db.backref('offer_photos', lazy=True))

    def serialize(self):
        return {
            'id': self.id,
            'offer_id': self.offer_id,
            'photo_url': self.photo_url,
            'is_primary': self.is_primary
        }