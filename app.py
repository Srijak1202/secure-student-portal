from flask import Flask, redirect, url_for, session
from flask_login import LoginManager
from models import db, User
from datetime import timedelta
import os

def create_app():
    app = Flask(__name__)
    
    # Configuration
    app.config['SECRET_KEY'] = 'dev-secret-key-change-in-prod' # In real app use random hex
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///academic_monitoring.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=20)

    # Initialize Extensions
    db.init_app(app)
    
    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)

    @app.before_request
    def make_session_permanent():
        session.permanent = True

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Register Blueprints
    from routes.auth_routes import auth_bp
    from routes.admin_routes import admin_bp
    from routes.faculty_routes import faculty_bp
    from routes.student_routes import student_bp
    from routes.advisor_routes import advisor_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(faculty_bp, url_prefix='/faculty')
    app.register_blueprint(student_bp, url_prefix='/student')
    app.register_blueprint(advisor_bp, url_prefix='/class_advisor')

    @app.route('/')
    def index():
        # Force logout on landing for demo purposes
        from flask_login import logout_user
        logout_user() 
        return redirect(url_for('auth.login'))

    # Prevent browser from caching pages - blocks back button after logout
    @app.after_request
    def add_no_cache_headers(response):
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        return response

    return app

if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        # Auto-create DB for convenience in this lab setting if not exists
        # But we will use init_db.py for better control
        pass
    app.run(debug=True)
