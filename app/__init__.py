from flask import Flask, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Config, Migrate
import os
from app.translations import translations

db = SQLAlchemy()
login_manager = LoginManager()


ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
def allowed_file(filename):
        return (
            '.' in filename and
            filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
        )


def create_app():
    app = Flask(__name__)
    app.config.from_object('config.Config')
    UPLOAD_FOLDER2 = os.path.join('app','static', 'uploads', 'diseases')
    os.makedirs(UPLOAD_FOLDER2, exist_ok=True)
    app.config['UPLOAD_FOLDER2'] = UPLOAD_FOLDER2
    
    
    db.init_app(app)
    login_manager.init_app(app)





    @app.context_processor
    def inject_translations():
        lang = session.get("lang", "en")
        return {"t": translations.get(lang, translations["en"])}

    from .routes import auth, admin, disease, detect, dashboard, lang
    app.register_blueprint(auth.bp)
    app.register_blueprint(admin.bp)
    app.register_blueprint(disease.bp)
    app.register_blueprint(detect.bp)
    app.register_blueprint(dashboard.bp)
    app.register_blueprint(lang.bp)

    return app

