from flask import Blueprint, render_template, redirect, url_for, flash, session, request
from flask_login import login_user, logout_user, login_required, current_user
from models import User, StudentProfile, db
from utils.auth import verify_password, generate_otp, verify_otp, hash_password
from datetime import datetime, timedelta

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for(f'{current_user.role}.dashboard'))
        
    if request.method == 'POST':
        username = request.form.get('username') # Roll No
        password = request.form.get('password')
        role = 'student' # Enforced
        
        # New Fields
        full_name = request.form.get('full_name')
        degree = request.form.get('degree')
        branch = request.form.get('branch')
        dob = request.form.get('dob')
        contact = request.form.get('contact')
        blood_group = request.form.get('blood_group')
        email = request.form.get('email')

        if User.query.filter_by(username=username).first():
            flash('Roll No already registered', 'error')
            return redirect(url_for('auth.register'))

        # Check: same email cannot be used for the same role twice
        if User.query.filter_by(email=email, role=role).first():
            flash('An account with this email already exists for this role.', 'error')
            return redirect(url_for('auth.register'))
            
        hashed_pw = hash_password(password)
        new_user = User(username=username, password_hash=hashed_pw, role=role, email=email)
        db.session.add(new_user)
        db.session.commit() # Commit to get ID
        
        # Create Profile
        new_profile = StudentProfile(
            user_id=new_user.id,
            full_name=full_name,
            degree=degree,
            branch=branch,
            course=f"{degree} {branch}",
            semester=1, # Default
            roll_no=username, # Sync with username
            dob=dob,
            contact=contact,
            blood_group=blood_group,
            email=email,
            risk_attendance="Safe",
            risk_marks="Safe"
        )
        db.session.add(new_profile)
        db.session.commit()
        
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('auth.login'))
        
    return render_template('register.html')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        # Redirect based on role if already logged in (and MFA done)
        if session.get('mfa_completed'):
            return redirect(url_for(f'{current_user.role}.dashboard'))
            
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        email_input = request.form.get('email')
        
        user = User.query.filter_by(username=username).first()

        # Check for Lockout
        if user and user.lockout_until:
            if datetime.utcnow() < user.lockout_until:
                flash('Account is locked due to multiple failed login attempts. Please try again later.', 'error')
                return redirect(url_for('auth.login'))
            else:
                # Lockout expired
                user.lockout_until = None
                user.failed_login_attempts = 0
                db.session.commit()
        
        if user and verify_password(user.password_hash, password):
            # Step 1.5: Verify Email Matches
            if user.email and user.email.lower() != email_input.lower():
                # Treat as failed attempt to prevent enumeration? Or just error.
                # For NIST, we should probably treat credential mismatch as failure.
                # But email is MFA step initiation here.
                # Let's count it as failed attempt to be safe against guessing.
                user.failed_login_attempts = (user.failed_login_attempts or 0) + 1
                db.session.commit()
                flash('Email verification failed. Email does not match our records.', 'error')
                return redirect(url_for('auth.login'))
            
            # Successful Login
            user.failed_login_attempts = 0
            user.lockout_until = None
            db.session.commit()
            
            # Step 1 Success: Login user but mark MFA as pending
            login_user(user)
            session['mfa_completed'] = False
            
            # Generate OTP
            otp = generate_otp(user.id)
            
            # Send Email (Real)
            from utils.email_sender import send_otp_email
            success, msg = send_otp_email(user.email, otp)
            
            if success:
                flash(f'OTP sent to {user.email}', 'info')
            else:
                # Security: Do NOT show OTP on screen.
                flash(f'Failed to send OTP email: {msg}. Check Sender Config.', 'error')
                return redirect(url_for('auth.login')) 
            
            return redirect(url_for('auth.mfa'))
        else:
            # Login Failed
            if user:
                user.failed_login_attempts = (user.failed_login_attempts or 0) + 1
                if user.failed_login_attempts >= 5:
                    user.lockout_until = datetime.utcnow() + timedelta(minutes=15)
                    flash('Account locked due to too many failed attempts.', 'error')
                else:
                    flash('Invalid username or password', 'error')
                db.session.commit()
            else:
                 flash('Invalid username or password', 'error')
            
    return render_template('login.html')

@auth_bp.route('/mfa', methods=['GET', 'POST'])
@login_required
def mfa():
    if session.get('mfa_completed'):
         return redirect(url_for(f'{current_user.role}.dashboard'))

    if request.method == 'POST':
        otp_code = request.form.get('otp')
        if verify_otp(current_user.id, otp_code):
            session['mfa_completed'] = True
            flash('Login Successful', 'success')
            return redirect(url_for(f'{current_user.role}.dashboard'))
        else:
            flash('Invalid or Expired OTP', 'error')
            
    return render_template('mfa.html')

@auth_bp.route('/logout')
@login_required
def logout():
    session.pop('mfa_completed', None)
    logout_user()
    flash('Logged out successfully', 'success')
    return redirect(url_for('auth.login'))

@auth_bp.route('/access_control')
def access_control():
    # Public route to view permissions matrix
    return render_template('access_control.html')

@auth_bp.route('/encoding_theory')
def encoding_theory():
    # Public route to view encoding theory
    return render_template('encoding_theory.html')
