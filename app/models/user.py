from app import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash



class User(db.Model, UserMixin):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)

    ROLE_TENANT = "tenant"
    ROLE_LANDLORD = "landlord"
    ROLE_ADMIN = "admin"

    role = db.Column(db.String(50), default=ROLE_TENANT, nullable=False)

    first_name = db.Column(db.String(50))
    last_name = db.Column(db.String(50))
    phone_number = db.Column(db.String(20))
    company_name = db.Column(db.String(100))
    contact_telegram = db.Column(db.Boolean, default=False)
    contact_viber = db.Column(db.Boolean, default=False)
    contact_whatsapp = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())


    def set_password(self, password: str):
        self.password_hash = generate_password_hash(password)

    def check_password(self, raw_password: str) -> bool:
        return check_password_hash(self.password_hash, raw_password)
    
    def has_role(self, *roles) -> bool:
        return self.role in roles

    def serialize(self) -> dict:
        return {
            'id': self.id,
            'email': self.email,
            'role': self.role,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'phone_number': self.phone_number,
            'company_name': self.company_name,
            'contact_telegram': self.contact_telegram,
            'contact_viber': self.contact_viber,
            'contact_whatsapp': self.contact_whatsapp,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }



