from app import db


class SavedOffer(db.Model):
    __tablename__ = 'saved_offers'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    offer_id = db.Column(db.Integer, db.ForeignKey('commercial_listings.id'), nullable=False)


    user = db.relationship('User', backref=db.backref('saved_offers', lazy=True))
    offer = db.relationship('CommLeasing', backref=db.backref('saved_by_users', lazy=True))

    def serialize(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'offer_id': self.offer_id
        }
    