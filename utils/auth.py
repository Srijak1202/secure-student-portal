from functools import wraps
from flask import abort, flash, redirect, url_for
from flask_login import current_user
from werkzeug.security import check_password_hash, generate_password_hash
import random
from datetime import datetime, timedelta
from models import OTP, db

def hash_password(password):
    """
    Hashes password with salt.
    Satisfies Requirement: Hashing
    """
    hashed = generate_password_hash(password, method='pbkdf2:sha256')
    print(f"\n[CRYPTO LOG] Hashing Password: '{password}' -> '{hashed}'")
    return hashed

def verify_password(hash, password):
    return check_password_hash(hash, password)

def role_required(*roles):
    """
    Decorator for Role-Based Access Control (RBAC).
    Satisfies Requirement: Authorization
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for('auth.login'))
            
            if current_user.role not in roles:
                # Access Denied
                abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def generate_otp(user_id):
    """
    Generates a 6-digit OTP and stores it.
    Satisfies Requirement: Multi-Factor Authentication
    """
    otp_code = str(random.randint(100000, 999999))
    expiry = datetime.utcnow() + timedelta(minutes=5)
    
    # Invalidate old OTPs
    old_otps = OTP.query.filter_by(user_id=user_id, is_used=False).all()
    for o in old_otps:
        o.is_used = True
    
    new_otp = OTP(user_id=user_id, otp_code=otp_code, expiry=expiry)
    db.session.add(new_otp)
    db.session.commit()
    
    # In a real app, send email/SMS here.
    # For this lab/demo, we log it effectively.
    print(f"[{datetime.now()}] MFA OTP for User ID {user_id}: {otp_code}")
    return otp_code

def verify_otp(user_id, otp_code):
    """
    Verifies OTP.
    Satisfies Requirement: Multi-Factor Authentication
    """
    otp_record = OTP.query.filter_by(user_id=user_id, otp_code=otp_code, is_used=False).first()
    
    if not otp_record:
        return False
        
    if datetime.utcnow() > otp_record.expiry:
        otp_record.is_used = True
        db.session.commit()
        return False
        
    # Mark used
    otp_record.is_used = True
    db.session.commit()
    return True
