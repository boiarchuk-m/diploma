from app.models.user import User
from app import db

class UsersService:

    @staticmethod
    def get_by_id(user_id: int) -> User | None:
        """Повертає користувача за ID або None."""
        return User.query.get(user_id)
    
    @staticmethod   
    def get_by_email(email: str) -> User | None:
        """Повертає користувача за email або None."""
        if not email:
            return None
        return User.query.filter_by(email=email.strip().lower()).first()
    
    
    @staticmethod
    def update_profile(user: User, new_data: dict) -> User:
        """Оновлює профіль користувача."""
        if 'first_name' in new_data:
            user.first_name = new_data['first_name']
        if 'last_name' in new_data:
            user.last_name = new_data['last_name']
        if 'phone_number' in new_data:
            user.phone_number = new_data['phone_number']
        if 'company_name' in new_data:
            user.company_name = new_data['company_name']    
        if 'contact_telegram' in new_data:
            user.contact_telegram = new_data['contact_telegram']
        if 'contact_viber' in new_data: 
            user.contact_viber = new_data['contact_viber']  
        if 'contact_whatsapp' in new_data:
            user.contact_whatsapp = new_data['contact_whatsapp']
        db.session.commit()
        return user
        
    
    @staticmethod
    def change_password(user: User, 
        old_password: str,
        new_password: str,
        confirm_password: str = None,
    ) -> None:
        
        if not old_password or not new_password:
            raise ValueError("Пароль не може бути порожнім")

        if not user.check_password(old_password):
            raise ValueError("Невірний поточний пароль")

        if confirm_password is not None and new_password != confirm_password:
            raise ValueError("Новий пароль та підтвердження не співпадають")

        user.set_password(new_password)
        db.session.commit()

    @staticmethod
    def change_role(user: User, new_role: str) -> None:
        """Змінює роль користувача."""

        if new_role == User.ROLE_ADMIN:
           
            raise ValueError("Заборонено змінювати роль на адміністраторську")
        
        user.role = new_role
        db.session.commit()
    