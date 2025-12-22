from flask import Blueprint, render_template, request, redirect, url_for, flash

from app.services.auth_service import AuthService
from flask_login import login_user, logout_user, login_required
from app.utils.decorators import roles_required
from app.models.user import User

auth_bp = Blueprint("auth", __name__)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        data = request.form
        email = data.get('email').strip()
        password = data.get('password', "")
        role_type = data.get('role_type', 'tenant')
        print(role_type)

        if role_type == "landlord":
            role = User.ROLE_LANDLORD
        else:
            role = User.ROLE_TENANT

        try:
            user = AuthService.register_user(email, password, role)
        except ValueError as e:
            flash(str(e), "danger")
            return render_template("register.html")
        
        flash("Реєстрація успішна. Ви увійшли в систему.", "success")
        login_user(user)

        if user.role == User.ROLE_LANDLORD:
            return redirect(url_for("profile.edit_profile"))
        else:
            print("Redirecting tenant to main page")
            return redirect(url_for("offer.index"))

    return render_template('register.html')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.form
        email = data.get('email').strip()
        password = data.get('password', "")

        user = AuthService.authenticate_user(email, password)
        if not user:
            flash("Невірний email або пароль.", "danger")
            return render_template("login.html", form_data={'email': email})
        
        login_user(user)
        flash("Вхід успішний.", "success")

        return redirect(url_for("offers.index"))


    return render_template('login.html', form_data={})
    

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash("Ви вийшли з системи.", "success")
    return redirect(url_for('offers.index'))
