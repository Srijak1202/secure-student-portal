from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required
from models import db, User, AccessControl
from utils.auth import role_required, hash_password

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/dashboard')
@login_required
@role_required('admin')
def dashboard():
    users = User.query.all()
    # Satisfies Requirement: Authorization (Admin -> Full access/User Management)
    return render_template('admin_dashboard.html', users=users)

@admin_bp.route('/add_user', methods=['POST'])
@login_required
@role_required('admin')
def add_user():
    username = request.form.get('username')
    password = request.form.get('password')
    role = request.form.get('role')
    subject = request.form.get('subject') # Optional for non-faculty
    email = request.form.get('email') # New: Email for MFA
    
    if User.query.filter_by(username=username).first():
        flash('Username already exists', 'error')
        return redirect(url_for('admin.dashboard'))
        
    hashed_pw = hash_password(password)
    new_user = User(username=username, password_hash=hashed_pw, role=role, subject=subject, email=email)
    db.session.add(new_user)
    db.session.commit()
    
    flash('User added successfully', 'success')
    return redirect(url_for('admin.dashboard'))

@admin_bp.route('/export_risk_report')
@login_required
@role_required('admin')
def export_risk_report():
    import csv
    import io
    from flask import make_response
    from models import StudentProfile
    
    # query at-risk students
    profiles = StudentProfile.query.filter(
        (StudentProfile.risk_attendance != 'Safe') | 
        (StudentProfile.risk_marks != 'Safe')
    ).all()
    
    si = io.StringIO()
    cw = csv.writer(si)
    # Header
    cw.writerow(['Full Name', 'Roll No', 'Attendance Risk', 'Marks Risk', 'Email'])
    
    for p in profiles:
        cw.writerow([p.full_name, p.roll_no, p.risk_attendance, p.risk_marks, p.email])
        
    output = make_response(si.getvalue())
    output.headers["Content-Disposition"] = "attachment; filename=at_risk_students.csv"
    output.headers["Content-type"] = "text/csv"
    return output
