from flask import Blueprint, Config, app, current_app, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.models import DetectionLog, Disease
from app import db, allowed_file
import os
from werkzeug.utils import secure_filename
from flask_migrate import Migrate

bp = Blueprint('disease', __name__, url_prefix='/disease')

def admin_or_researcher_required(f):
    from functools import wraps
    @wraps(f)
    def wrapper(*args, **kwargs):
        if current_user.role not in ['Admin', 'Expert']:
            flash("Access denied.")
            return redirect(url_for('detect.detect'))
        return f(*args, **kwargs)
    return wrapper

@bp.route('/')
@login_required
@admin_or_researcher_required
def list_diseases():
    diseases = Disease.query.all()
    return render_template('disease/list.html', diseases=diseases)

@bp.route('/create', methods=['GET', 'POST'])
@login_required
@admin_or_researcher_required
def create_disease():
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        symptoms = request.form['symptoms']
        treatment = request.form['treatment']
        file = request.files.get('image')

        filename = None
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            save_dir = current_app.config['UPLOAD_FOLDER2']
            os.makedirs(save_dir, exist_ok=True)  # ensure directory exists
            file.save(os.path.join(save_dir, filename))
            image_path = f"uploads/diseases/{filename}"  # relative path for url_for('static', ...)

        disease = Disease(name=name, description=description,symptoms=symptoms, treatment=treatment, image_path=image_path)
        db.session.add(disease)
        db.session.commit()
        flash('Disease created successfully!', 'success')
        return redirect(url_for('disease.list_diseases'))

    return render_template('disease/create.html')


@bp.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_or_researcher_required
def edit_disease(id):
    disease = Disease.query.get_or_404(id)

    if request.method == 'POST':
        disease.name = request.form['name']
        disease.description = request.form['description']
        disease.symptoms = request.form['symptoms']
        disease.treatment = request.form['treatment']
        file = request.files.get('image')

        if file and allowed_file(file.filename):
            # Delete old image file if exists
            if disease.image_path:
                old_image_path = os.path.join(current_app.root_path, 'static', disease.image_path)
                if os.path.exists(old_image_path):
                    os.remove(old_image_path)

            # Save new image
            filename = secure_filename(file.filename)
            save_dir = current_app.config['UPLOAD_FOLDER2']
            os.makedirs(save_dir, exist_ok=True)  # ensure directory exists
            file.save(os.path.join(save_dir, filename))

            disease.image_path = f"uploads/diseases/{filename}"

        db.session.commit()
        flash('Disease updated successfully!', 'success')
        return redirect(url_for('disease.list_diseases'))

    return render_template('disease/edit.html', disease=disease)

@bp.route('/delete/<int:id>')
@login_required
@admin_or_researcher_required
def delete_disease(id):
    disease = Disease.query.get_or_404(id)

    # Delete image file if exists
    if disease.image_path:
        image_path = os.path.join(current_app.root_path, 'static', disease.image_path)
        if os.path.exists(image_path):
            os.remove(image_path)

    db.session.delete(disease)
    db.session.commit()

    flash('Disease deleted successfully!', 'success')
    return redirect(url_for('disease.list_diseases'))

