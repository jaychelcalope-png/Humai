from flask import Blueprint, render_template, redirect, request, url_for, flash
from flask_login import login_required, current_user
from app.models import User
from app import db
from werkzeug.security import generate_password_hash

bp = Blueprint('admin', __name__, url_prefix='/admin')

def admin_required(f):
    from functools import wraps
    @wraps(f)
    def wrapper(*args, **kwargs):
        if current_user.role != 'Admin':
            flash("Admin access only.")
            return redirect(url_for('detect.detect'))
        return f(*args, **kwargs)
    return wrapper

@bp.route('/users')
@login_required
@admin_required
def manage_users():
    users = User.query.all()
    return render_template('admin/users.html', users=users)

@bp.route('/users/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create_user():
    if request.method == 'POST':
        username = request.form['username']
        role = request.form['role']
        password = request.form['password']

        if User.query.filter_by(username=username).first():
            flash("Username already exists.")
            return redirect(url_for('admin.create_user'))

        new_user = User(
            username=username,
            role=role,
            password=generate_password_hash(password)
        )
        db.session.add(new_user)
        db.session.commit()
        flash("User created.")
        return redirect(url_for('admin.manage_users'))

    return render_template('admin/user_form.html', user=None)

@bp.route('/users/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_user(id):
    user = User.query.get_or_404(id)
    if request.method == 'POST':
        user.username = request.form['username']
        user.role = request.form['role']
        db.session.commit()
        flash("User updated.")
        return redirect(url_for('admin.manage_users'))
    return render_template('admin/user_form.html', user=user)

@bp.route('/users/delete/<int:id>')
@login_required
@admin_required
def delete_user(id):
    user = User.query.get_or_404(id)
    if user.id == current_user.id:
        flash("You cannot delete yourself.")
    else:
        db.session.delete(user)
        db.session.commit()
        flash("User deleted.")
    return redirect(url_for('admin.manage_users'))