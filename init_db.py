from app import create_app
from models import db, User, AccessControl, StudentProfile, Attendance, RiskThreshold, AcademicRecord
from utils.auth import hash_password
from utils.crypto import encrypt_data, sign_data

def init_db():
    app = create_app()
    with app.app_context():
        # Drop all to ensure schema update - WARNING: DATA LOSS in Dev
        db.drop_all()
        db.create_all()
        
        print("Creating users and profiles...")
        
        # 1. Users
        # 1. Users
        admin = User(username='admin', password_hash=hash_password('admin123'), role='admin', email='srijak1202@gmail.com')
        faculty = User(username='faculty', password_hash=hash_password('faculty123'), role='faculty', subject='Cyber Security', email='faculty@univ.edu') 
        advisor = User(username='advisor', password_hash=hash_password('advisor123'), role='class_advisor', subject='Class B', email='advisor@univ.edu')
        student = User(username='student', password_hash=hash_password('student123'), role='student', email='john@univ.edu')
        
        db.session.add_all([admin, faculty, advisor, student])
        db.session.commit() # Commit to get IDs
        
        # 2. Student Profile (Detailed)
        s_profile = StudentProfile(
            user_id=student.id,
            full_name="John Doe",
            degree="B.Tech",
            branch="CSE",
            course="B.Tech CSE",
            semester=6,
            cgpa=7.2,
            current_sgpa=7.5,
            email="john@univ.edu",
            contact="9876543210",
            roll_no="CB.EN.U4CSE21001",
            dob="2003-05-15",
            blood_group="O+",
            risk_attendance="Safe",
            risk_marks="Safe"
        )
        db.session.add(s_profile)
        
        # 3. Attendance Data (counters init)
        # 17/20 = 85%
        att1 = Attendance(student_id=student.id, subject="Cyber Security", percentage=85.0, month="January", classes_conducted=20, classes_attended=17)
        # 12/20 = 60%
        # att2 = Attendance(student_id=student.id, subject="Compiler Design", percentage=60.0, month="January", classes_conducted=20, classes_attended=12) 
        db.session.add_all([att1])
        
        # 4. Academic Records
        marks = "45"
        risk = "80"
        enc_marks = encrypt_data(marks)
        enc_risk = encrypt_data(risk)
        sig = sign_data(f"{student.id}Compiler Design{marks}{risk}")
        
        # 5. Risk Thresholds
        
        # 5. Risk Thresholds
        t1 = RiskThreshold(metric_name='min_attendance', value=75.0, risk_level='Medium')
        t2 = RiskThreshold(metric_name='critical_attendance', value=65.0, risk_level='High')
        t3 = RiskThreshold(metric_name='min_cgpa', value=6.0, risk_level='High')
        db.session.add_all([t1, t2, t3])
        
        # 6. Access Control
        ac1 = AccessControl(role='admin', resource='all', permission='full')
        ac2 = AccessControl(role='faculty', resource='academic', permission='write')
        ac3 = AccessControl(role='student', resource='own_data', permission='read')
        ac4 = AccessControl(role='class_advisor', resource='class_data', permission='write')
        db.session.add_all([ac1, ac2, ac3, ac4])
        
        db.session.commit()
        print("Database initialized with Phase 2 data! Users: admin, faculty, student (pass: role123)")

if __name__ == '__main__':
    init_db()
