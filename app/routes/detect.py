import os
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.models import DetectionLog, Disease
from app import db
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing import image
import numpy as np
import os

bp = Blueprint('detect', __name__, url_prefix='/detect')

# Load trained model once
#MODEL = load_model('rice_model.h5')

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

MODEL_PATH = os.path.join(BASE_DIR, "rice_model.h5")
MODEL_PATH = os.path.abspath(MODEL_PATH)
print("Loading model from:", MODEL_PATH)

# Labels used in predictions
LABELS = [
    'Bacterial Leaf Blight',
    'Brown_Spot',
    'Healthy Rice Leaf',
    'Rice Blast',
    'Rice Tungro',
    'Not Rice Leaf'
]

# -------------------------------#
#        DETECTION PAGE          #
# -------------------------------#
@bp.route('/', methods=['GET', 'POST'])
def detect():
    result = None
    confidence = None
    disease = None

    # If logged in, show personal logs
    if current_user.is_authenticated:
        page = request.args.get('page', 1, type=int)
        logs = DetectionLog.query.filter_by(user_id=current_user.id) \
            .order_by(DetectionLog.timestamp.desc()) \
            .paginate(page=page, per_page=5)
    else:
      logs = DetectionLog.query.order_by(DetectionLog.timestamp.desc()).limit(5).all()

    if request.method == 'POST':
        img_file = request.files.get('image')
        if img_file:
            # Save uploaded image
            save_path = os.path.join('app/static/uploads', img_file.filename)
            img_file.save(save_path)

            # Preprocess
            img = image.load_img(save_path, target_size=(224, 224))
            x = image.img_to_array(img)
            x = np.expand_dims(x, axis=0)
            x /= 255.0

            # Predict
            prediction = MODEL.predict(x)
            pred_index = np.argmax(prediction)
            pred_label = LABELS[pred_index]
            pred_conf = float(prediction[0][pred_index]) * 100

            # Prepare image path (relative)
            relative_path = os.path.relpath(save_path, "static").replace("\\", "/")

            # -----------------#
            # SAVE TO DATABASE #
            # -----------------#
            user_id = current_user.id if current_user.is_authenticated else None

            log = DetectionLog(
                image_path=relative_path,
                result=pred_label,
                confidence=pred_conf,
                user_id=user_id
            )

            db.session.add(log)
            db.session.commit()

            # Fetch disease treatment info
            disease = Disease.query.filter_by(name=pred_label).first()

            # Set output display
            result = pred_label
            confidence = pred_conf

    return render_template(
        'detect.html',
        result=result,
        confidence=confidence,
        disease=disease,
        logs=logs
    )

# -------------------------------#
#      VIEW DETECTION LOGS       #
# -------------------------------#
@bp.route('/logs')
@login_required
def logs():
    page = request.args.get('page', 1, type=int)

    logs = DetectionLog.query.filter_by(user_id=current_user.id) \
        .order_by(DetectionLog.timestamp.desc()) \
        .paginate(page=page, per_page=5)

    return render_template('logs.html', logs=logs)

