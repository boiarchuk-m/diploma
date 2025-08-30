from app import db


class Businesses(db.Model):
    __tablename__ = 'businesses'

    id = db.Column(db.Integer, primary_key=True)
    business = db.Column(db.String(100), nullable=False)
    squaremin = db.Column(db.Integer, nullable=False)
    squaremax = db.Column(db.Integer, nullable=False)
    wsquare = db.Column(db.Float, nullable=False)
    wcost = db.Column(db.Float, nullable=False)
    wtransport = db.Column(db.Float, nullable=False)
    wcompetitors = db.Column(db.Float, nullable=False)
    wbusinesses = db.Column(db.Float, nullable=False)


    def serialize(self):
        return {
            'id': self.id,
            'business': self.business,
            'squaremin': self.squareMin,
            'squaremax': self.squareMax,
            'wsquare': self.wsquare,
            'wcost': self.wcost,
            'wtransport': self.wtransport,
            'wcompetitors': self.competitors,
            'wbusinesses': self.wbusinesses

        }


