from app import db



class OfferPhoto(db.Model):
    __tablename__ = 'offer_photos'

    id = db.Column(db.Integer, primary_key=True)
    offer_id = db.Column(db.Integer, nullable=False)
    photo_url = db.Column(db.String(255), nullable=False)  
    is_primary = db.Column(db.Boolean, default=False)

    def serialize(self):
        return {
            'id': self.id,
            'offer_id': self.offer_id,
            'filename': self.filename,
            'is_primary': self.is_primary
        }