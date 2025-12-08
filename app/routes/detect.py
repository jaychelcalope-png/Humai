import os
from flask import Blueprint, render_template, request
from flask_login import login_required, current_user
from app.models import DetectionLog, Disease
from app import db
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing import image
import numpy as np

bp = Blueprint('detect', __name__, url_prefix='/detect')

# ------------------------------------
#        MODEL LOADING FIXED
# ------------------------------------

# Get the absolute directory of this file
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Build the absolute path to the model file
MODEL_PATH = os.path.join(BASE_DIR, "..", "rice_model.h5")

# Normalize for Linux/Windows compatibility
MODEL_PATH = os.path.normpath(MODEL_PATH)

print("Loading model from:", MODEL_PATH)

# Load the model safely
MODEL = load_model(MODEL_PATH)

# Labels
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

    # Logs depending on authentication
    if current_user.is_authenticated:
        page = request.args.get('page', 1, type=int)
        logs = (DetectionLog.query.filter_by(user_id=current_user.id)
                .order_by(DetectionLog.timestamp.desc())
                .paginate(page=page, per_page=5))
    else:
        logs = (DetectionLog.query.order_by(DetectionLog.timestamp.desc())
                .limit(5)
                .all())

    if request.method == 'POST':
        img_file = request.files.get('image')
        if img_file:

            # Upload path (absolute)
            upload_dir = os.path.join(BASE_DIR, "..", "static", "uploads")
            os.makedirs(upload_dir, exist_ok=True)

            save_path = os.path.join(upload_dir, img_file.filename)
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

            # Relative path for HTML
            relative_path = f"uploads/{img_file.filename}"

            # Save to DB
            user_id = current_user.id if current_user.is_authenticated else None
            log = DetectionLog(
                image_path=relative_path,
                result=pred_label,
                confidence=pred_conf,
                user_id=user_id
            )

            db.session.add(log)
            db.session.commit()

            # Fetch disease info
            disease = Disease.query.filter_by(name=pred_label).first()

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

    logs = (DetectionLog.query.filter_by(user_id=current_user.id)
            .order_by(DetectionLog.timestamp.desc())
            .paginate(page=page, per_page=5))

    return render_template('logs.html', logs=logs)
