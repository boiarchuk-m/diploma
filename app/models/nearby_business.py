from app import db


class NearbyBusiness(db.Model):
    __tablename__ = 'nearby_businesses'

    offer_id = db.Column(db.Integer, primary_key=True)
    stops = db.Column(db.Integer, nullable=False)
    cafes = db.Column(db.Integer, nullable=False)
    restaurants = db.Column(db.Integer, nullable=False)
    bars_pubs = db.Column(db.Integer, nullable=False)
    pharmacies = db.Column(db.Integer, nullable=False)
    beauty_salons = db.Column(db.Integer, nullable=False)
    grocery_stores = db.Column(db.Integer, nullable=False)
    clothing_shops = db.Column(db.Integer, nullable=False)
    flower_shops = db.Column(db.Integer, nullable=False)
    pet_shops = db.Column(db.Integer, nullable=False)
    ateliers = db.Column(db.Integer, nullable=False)
    repair_services = db.Column(db.Integer, nullable=False)
    gyms = db.Column(db.Integer, nullable=False)


    def serialize(self):
        return {
            'offer_id': self.offer_id,
            'stops': self.stops,
            'cafes': self.cafes,
            'restaurants': self.restaurants,
            'bars_pubs': self.bars_pubs,
            'pharmacies':self.pharmacies,
            'beauty_salons': self.beauty_salons,
            'grocery_stores': self.grocery_stores,
            'clothing_shops': self.clothing_shops,
            'flower_shops':self.flower_shops,
            'pet_shops': self.pet_shops,
            'ateliers': self.ateliers,
            'repair_services': self.repair_services,
            'gyms' :self.gyms

        }


