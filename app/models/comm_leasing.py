from app import db


class CommLeasing(db.Model):
    __tablename__ = 'commercial_listings'

    id = db.Column(db.Integer, primary_key=True)
    address = db.Column(db.String(255), nullable=False)
    district = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Integer, nullable=False)  # грн/місяць
    area = db.Column(db.Integer, nullable=False)  # м²
    description = db.Column(db.Text)
    repair = db.Column(db.String(50))
    recommended_for = db.Column(db.String(255))

    def serialize(self):
        return {
            'id': self.id,
            'address': self.address,
            'district': self.district,
            'price': self.price,
            'area': self.area,
            'description': self.description,
            'repair': self.repair,
            'recommended_for': self.recommended_for

        }

