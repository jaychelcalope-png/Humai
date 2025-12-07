from app import create_app, db
from app.models import User
from werkzeug.security import generate_password_hash

app = create_app()

with app.app_context():
    db.create_all()  # Ensure tables exist

    username = 'admin'
    password = 'admin123'
    role = 'Admin'

    if not User.query.filter_by(username=username).first():
        admin_user = User(
            username=username,
            role=role,
            password=generate_password_hash(password)
        )
        db.session.add(admin_user)
        db.session.commit()
        print(f'✅ Admin user "{username}" created with password: {password}')
    else:
        print(f'⚠️ Admin user "{username}" already exists.')
