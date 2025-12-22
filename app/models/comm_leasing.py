from app import db


class CommLeasing(db.Model):
    __tablename__ = 'commercial_listings'

    id = db.Column(db.Integer, primary_key=True)
    address = db.Column(db.String(255), nullable=False)
    district = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Integer, nullable=False)  
    area = db.Column(db.Integer, nullable=False)  
    description = db.Column(db.Text)
    repair = db.Column(db.String(50))
    city =db.Column(db.String(100))
    recommended_for = db.Column(db.String(255), nullable=True)
    stops_num = db.Column(db.Integer, nullable=True)
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    approved = db.Column(db.Boolean, default=False)
    comment = db.Column(db.Text, nullable=True)

    owner = db.relationship('User', backref=db.backref('commercial_listings', lazy=True))

    def serialize(self):
        return {
            'id': self.id,
            'address': self.address,
            'district': self.district,
            'price': self.price,
            'area': self.area,
            'description': self.description,
            'repair': self.repair,
            'city': self.city,
            'recommended_for': self.recommended_for,
            'stops_num': self.stops_num,
            'owner_id': self.owner_id,
            'approved': self.approved

        }

