from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'admin', 'faculty', 'student'
    email = db.Column(db.String(150)) # New: For MFA
    subject = db.Column(db.String(100)) # New: Assigned Subject for Faculty
    
    # Account Lockout
    failed_login_attempts = db.Column(db.Integer, default=0)
    lockout_until = db.Column(db.DateTime, nullable=True)

    # Relationships
    profile = db.relationship('StudentProfile', backref='user', uselist=False, cascade="all, delete-orphan")
    academic_records = db.relationship('AcademicRecord', backref='student', lazy=True)
    attendance_records = db.relationship('Attendance', backref='student', lazy=True)
    mentoring_logs = db.relationship('MentoringLog', foreign_keys='MentoringLog.student_id', backref='student_ref', lazy=True)

class StudentProfile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), unique=True, nullable=False)
    full_name = db.Column(db.String(150))
    degree = db.Column(db.String(50)) # e.g. B.Tech
    branch = db.Column(db.String(50)) # e.g. CSE
    course = db.Column(db.String(50)) # Keeping for backward compat, or alias to Degree
    semester = db.Column(db.Integer)
    semester = db.Column(db.Integer)
    section = db.Column(db.String(10)) # New: Class Section (e.g. 'A', 'B')
    cgpa = db.Column(db.Float)
    sgpa = db.Column(db.Text, default="0.0") 
    current_sgpa = db.Column(db.Float)
    
    # Extended Details
    email = db.Column(db.String(150))
    contact = db.Column(db.String(20))
    roll_no = db.Column(db.String(20))
    dob = db.Column(db.String(20)) 
    blood_group = db.Column(db.String(5))
    profile_pic = db.Column(db.String(255), default='default_avatar.png')
    
    parent_email = db.Column(db.String(150))
    
    # Risk Levels (Split)
    risk_attendance = db.Column(db.String(20), default='Safe')
    risk_marks = db.Column(db.String(20), default='Safe')
    
    # Class Advisor Fields
    grace_marks = db.Column(db.Float, default=0.0)
    advisor_remarks = db.Column(db.Text)

class AcademicRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    semester = db.Column(db.Integer, nullable=False, default=1)
    subject = db.Column(db.String(100), nullable=False)
    
    # New Detailed Columns
    assignments = db.Column(db.String(200)) # e.g., "A1: 10/10, A2: 8/10"
    evaluations = db.Column(db.String(200)) # e.g., "Midterm: 40/50"
    remarks = db.Column(db.Text)
    
    # Encrypted fields
    marks_encrypted = db.Column(db.Text, nullable=False) # Internal Marks
    risk_score_encrypted = db.Column(db.Text, nullable=False)
    
    signature = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Attendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    subject = db.Column(db.String(100), nullable=False)
    percentage = db.Column(db.Float, nullable=False, default=0.0)
    month = db.Column(db.String(20)) 
    
    # Daily Tracking Counters
    classes_conducted = db.Column(db.Integer, default=0)
    classes_attended = db.Column(db.Integer, default=0)
    last_marked_date = db.Column(db.String(20))  # Track last marked date to prevent duplicates

class AttendanceLog(db.Model):
    """Individual daily attendance entries for detailed tracking."""
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    subject = db.Column(db.String(100), nullable=False)
    date = db.Column(db.String(20), nullable=False)
    status = db.Column(db.String(10), nullable=False)  # 'Present' or 'Absent'
    slots = db.Column(db.Integer, default=1)

class MentoringLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    mentor_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    session_date = db.Column(db.DateTime, default=datetime.utcnow)
    issue = db.Column(db.Text, nullable=False)
    action_taken = db.Column(db.Text)
    status = db.Column(db.String(20), default='Pending') # Pending, Completed

class RiskThreshold(db.Model):
    """
    Admin configurable thresholds.
    """
    id = db.Column(db.Integer, primary_key=True)
    metric_name = db.Column(db.String(50), unique=True) # e.g., 'min_attendance', 'min_cgpa'
    value = db.Column(db.Float, nullable=False)
    risk_level = db.Column(db.String(20)) # The risk level if this threshold is breached

class AccessControl(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    role = db.Column(db.String(20), nullable=False)
    resource = db.Column(db.String(50), nullable=False)
    permission = db.Column(db.String(10), nullable=False)

class OTP(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    otp_code = db.Column(db.String(6), nullable=False)
    expiry = db.Column(db.DateTime, nullable=False)
    is_used = db.Column(db.Boolean, default=False)
