from app import db

class NumBusinesses(db.Model):
    __tablename__ = 'num_businesses'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    offer_id = db.Column(db.Integer, nullable=False)
    business_type_id = db.Column(db.Integer, nullable=False)
    number = db.Column(db.Integer, nullable=False)

    def serialize(self):
        return {
            'id': self.id,
            'offer_id': self.offer_id,
            'business_type_id': self.business_type_id,
            'number': self.number
        }