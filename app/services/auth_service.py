from app import db
from app.models.user import User


class AuthService:

    @staticmethod
    def register_user(email: str, password: str, role: str = User.ROLE_TENANT) -> User:
        """Реєструє нового користувача."""

        existing = User.query.filter_by(email=email).first()
        if existing:
            raise ValueError("Користувач з таким email вже існує")

        if role == User.ROLE_ADMIN:
            role = User.ROLE_TENANT  # Забороняємо реєстрацію адміністраторів через цей метод
        
        user = User(email=email, role=role)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        return user
    
    @staticmethod
    def authenticate_user(email: str, password: str) -> User | None:
        """Аутентифікує користувача за email та паролем."""

        if not email or not password:
            return None
        email = email.strip().lower()
        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            return user
        return None