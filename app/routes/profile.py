from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user

from app.utils.decorators import roles_required
from app.models.user import User
from app.services.users_service import UsersService

profile_bp = Blueprint("profile", __name__)




@profile_bp.route('/profile', methods=['GET'])
@login_required
def profile_view():
    return render_template('profile_view.html', user=current_user)


@profile_bp.route('/profile/edit', methods=['GET', 'POST'])
@roles_required(User.ROLE_LANDLORD)

def edit_profile():
    if request.method == 'POST':
        data= {
            'first_name': request.form.get('first_name'),
            'last_name': request.form.get('last_name'),
            'phone_number': request.form.get('phone_number'),
            'company_name': request.form.get('company_name'),
            'contact_telegram': bool(request.form.get('contact_telegram')),
            'contact_viber': bool(request.form.get('contact_viber')),
            'contact_whatsapp': bool(request.form.get('contact_whatsapp')),
        }

        user = UsersService.update_profile(current_user, data)
        flash("Профіль оновлено успішно.", "success")
        return redirect(url_for('offers.index'))
    return render_template('profile.html', user=current_user)


@profile_bp.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    if request.method == 'POST':
        current_password = request.form.get('current_password', "")
        new_password = request.form.get('new_password', "")
        confirm_password = request.form.get('confirm_password', "")

        if not request.user.check_password(current_password):
            flash("Поточний пароль невірний.", "danger")
            return render_template('change_password.html')

        if new_password != confirm_password:
            flash("Новий пароль та підтвердження не співпадають.", "danger")
            return render_template('change_password.html', user=current_user)

        try:
            UsersService.change_password(
                request.user, 
                current_password, 
                new_password, 
                confirm_password)
        except ValueError as e:
            flash(str(e), "danger")
            return render_template('password.html', user=current_user)
        flash("Пароль успішно змінено.", "success")

        return redirect(url_for('profile.profile_view'))

    return render_template('password.html', user=current_user)


@profile_bp.route('/change_role', methods=['POST'])
@login_required
def change_role():
    new_role = request.form.get('new_role', "")
    try:
        UsersService.change_role(request.user, new_role)
    except ValueError as e:
        flash(str(e), "danger")
        return redirect(url_for('profile.edit_profile'))

    flash("Роль успішно змінена.", "success")
    return redirect(url_for('offers.index'))
