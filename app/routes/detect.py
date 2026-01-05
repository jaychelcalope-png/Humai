import os
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app, send_from_directory, jsonify
from flask_login import login_required, current_user
from app.models import DetectionLog, Disease
from app import db
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing import image
import numpy as np
import tempfile
from werkzeug.utils import secure_filename

bp = Blueprint('detect', __name__, url_prefix='/detect')

MODEL = load_model('rice_model.h5')

LABELS = [
    'Bacterial Leaf Blight',
    'Brown_Spot',
    'Healthy Rice Leaf',
    'Rice Blast',
    'Rice Tungro',
    'Not Rice Leaf'
]

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

def allowed_file(filename):
    return '.' in filename and '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# -----------------------------------
# TEMPORARY UPLOAD FOLDER FOR DETECTION (mobile-friendly)
# -----------------------------------
def get_temp_upload_dir():
    save_dir = os.path.join(tempfile.gettempdir(), 'detection')
    os.makedirs(save_dir, exist_ok=True)
    return save_dir

# -----------------------------------
# ROUTE TO SERVE TEMP IMAGES (optional)
# -----------------------------------
@bp.route('/uploads/<filename>')
def uploaded_file(filename):
    save_dir = get_temp_upload_dir()
    return send_from_directory(save_dir, filename)

# -----------------------------------
# DETECTION PAGE
# -----------------------------------
@bp.route('/', methods=['GET', 'POST'])
def detect():
    result = None
    confidence = None
    disease = None

    # Logs (User or Guest)
    if current_user.is_authenticated:
        page = request.args.get('page', 1, type=int)
        logs = DetectionLog.query.filter_by(user_id=current_user.id) \
            .order_by(DetectionLog.timestamp.desc()) \
            .paginate(page=page, per_page=5)
    else:
        logs = DetectionLog.query.order_by(DetectionLog.timestamp.desc()).limit(5).all()

    # HANDLE IMAGE UPLOAD
    if request.method == 'POST':
        img_file = request.files.get('image')

        if img_file and allowed_file(img_file.filename):
            # Decide folder: TEMP for camera capture, else static/uploads for Add Disease
            if "capture_" in img_file.filename:  # camera capture
                save_dir = get_temp_upload_dir()
            else:
                save_dir = os.path.join(current_app.root_path, 'static/uploads')

            os.makedirs(save_dir, exist_ok=True)
            filename = secure_filename(img_file.filename)
            save_path = os.path.join(save_dir, filename)
            img_file.save(save_path)

            # Image preprocessing
            img = image.load_img(save_path, target_size=(224, 224))
            x = image.img_to_array(img)
            x = np.expand_dims(x, axis=0)
            x /= 255.0

            # Prediction
            prediction = MODEL.predict(x)
            pred_index = np.argmax(prediction)
            pred_label = LABELS[pred_index]
            pred_conf = float(prediction[0][pred_index]) * 100

            # Save to DB
            user_id = current_user.id if current_user.is_authenticated else None
            relative_path = os.path.relpath(save_path, os.path.join(current_app.root_path, 'static')).replace("\\", "/")

            log = DetectionLog(
                image_path=relative_path,
                result=pred_label,
                confidence=pred_conf,
                user_id=user_id
            )
            db.session.add(log)
            db.session.commit()

            # Save to session for GET display
            disease_obj = Disease.query.filter_by(name=pred_label).first()
            session['last_result'] = pred_label
            session['last_confidence'] = pred_conf
            session['last_disease_id'] = disease_obj.id if disease_obj else None

            return redirect(url_for('detect.detect'))

    # GET RESULT FROM SESSION
    result = session.pop('last_result', None)
    confidence = session.pop('last_confidence', None)
    disease_id = session.pop('last_disease_id', None)
    disease = Disease.query.get(disease_id) if disease_id else None

    return render_template(
        'detect.html',
        result=result,
        confidence=confidence,
        disease=disease,
        logs=logs,
    )

# -----------------------------------
# VIEW DETECTION LOGS
# -----------------------------------
@bp.route('/logs')
@login_required
def logs():
    page = request.args.get('page', 1, type=int)

    logs = DetectionLog.query.filter_by(user_id=current_user.id) \
        .order_by(DetectionLog.timestamp.desc()) \
        .paginate(page=page, per_page=10)

    return render_template('logs.html', logs=logs)
