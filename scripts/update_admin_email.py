import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from models import db, User

app = create_app()
with app.app_context():
    u = User.query.filter_by(username='admin').first()
    if not u:
        print('NO_ADMIN_FOUND')
    else:
        u.email = 'srijak1202@gmail.com'
        db.session.commit()
        print('UPDATED', u.username, u.email)
