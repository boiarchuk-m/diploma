from app import db


class RecommendedBusiness(db.Model):
    __tablename__ = 'recommended_business'

    id = db.Column(db.Integer, primary_key=True)
    listing_id = db.Column(db.Integer, db.ForeignKey('commercial_listings.id'), nullable=False)
    type_id = db.Column(db.Integer, db.ForeignKey('business_types.id'), nullable=False)


    listing = db.relationship('CommLeasing', backref=db.backref('recommended_businesses', lazy=True))
    business_type = db.relationship('Business_type', backref=db.backref('recommended_businesses', lazy=True))

    def serialize(self):
        return {
            'id': self.id,
            'listing_id': self.listing_id,
            'type_id': self.type_id
        }