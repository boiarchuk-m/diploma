from app import db


class Business_type(db.Model):
    __tablename__ = 'business_types'

    id = db.Column(db.Integer, primary_key=True)
    business_type = db.Column(db.String(100), nullable=False)
    min_area = db.Column(db.Integer, nullable=False)
    max_area = db.Column(db.Integer, nullable=False)
    w_area = db.Column(db.Float, nullable=False)
    w_price = db.Column(db.Float, nullable=False)
    w_stops = db.Column(db.Float, nullable=False)
    w_competitors = db.Column(db.Float, nullable=False)
    w_otherbiz = db.Column(db.Float, nullable=False)


    def serialize(self):
        return {
            'id': self.id,
            'business_type': self.business_type,
            'min_area': self.min_area,
            'max_area': self.max_area,
            'w_area': self.w_area,
            'w_price': self.w_price,
            'w_stops': self.w_stops,
            'w_competitors': self.w_competitors,
            'w_otherbiz': self.w_otherbiz

        }


