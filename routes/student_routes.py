from flask import Blueprint, render_template, flash, request, redirect, url_for
from flask_login import login_required, current_user
from models import db, AcademicRecord, StudentProfile, Attendance, AttendanceLog
from utils.auth import role_required
from utils.crypto import decrypt_data, verify_signature, encode_base64, decode_base64, sign_data
from utils.risk_engine import update_student_risk
from datetime import datetime

student_bp = Blueprint('student', __name__)

@student_bp.route('/dashboard')
@login_required
@role_required('student')
def dashboard():
    # 1. Update & Get Risk (Split)
    r_att, r_marks, factors = update_student_risk(current_user.id)
    
    # 2. Get Profile & Attendance
    profile = StudentProfile.query.filter_by(user_id=current_user.id).first()
    attendance_records = Attendance.query.filter_by(student_id=current_user.id).all()
    
    # 3. Get Academic Records
    records = AcademicRecord.query.filter_by(student_id=current_user.id).all()
    
    decrypted_records = []
    for record in records:
        marks = decrypt_data(record.marks_encrypted)
        risk_score = decrypt_data(record.risk_score_encrypted)
        
        raw_data = f"{record.student_id}{record.subject}{marks}{risk_score}"
        is_valid = verify_signature(raw_data, record.signature)
        
        decrypted_records.append({
            'subject': record.subject,
            'assignments': record.assignments,
            'evaluations': record.evaluations,
            'remarks': record.remarks,
            'marks': marks,
            'semester': record.semester,
            'is_valid': is_valid
        })
        
    # Calculate per-subject marks with risk levels
    subject_marks = {}
    for r in decrypted_records:
        subj = r['subject']
        if subj not in subject_marks:
            subject_marks[subj] = {'obtained': 0, 'total': 0}
        
        # Parse obtained/total from assignments or evaluations text
        text = r.get('assignments') or r.get('evaluations') or ""
        parsed = False
        if '/' in text:
            try:
                val_part = text.split(':')[-1].strip()
                if '->' in val_part:
                    converted = val_part.split('->')[-1].strip()
                    parts = converted.split('/')
                else:
                    parts = val_part.split('/')
                obt = float(parts[0].strip())
                tot = float(parts[1].strip())
                if tot > 0:
                    subject_marks[subj]['obtained'] += obt
                    subject_marks[subj]['total'] += tot
                    parsed = True
            except (ValueError, IndexError):
                pass
        
        if not parsed:
            try:
                subject_marks[subj]['obtained'] += float(r['marks'])
                subject_marks[subj]['total'] += 100
            except (ValueError, TypeError):
                pass
    
    # Build subject-wise summary with risk
    subject_summary = []
    grand_total = 0
    for subj, vals in subject_marks.items():
        pct = (vals['obtained'] / vals['total'] * 100) if vals['total'] > 0 else 0
        if pct >= 70:
            risk = 'Safe'
        elif pct >= 40:
            risk = 'Medium'
        else:
            risk = 'High'
        subject_summary.append({
            'subject': subj,
            'obtained': vals['obtained'],
            'total': vals['total'],
            'percentage': round(pct, 1),
            'risk': risk
        })
        grand_total += vals['obtained']

    # Fetch daily attendance logs grouped by subject
    daily_logs = AttendanceLog.query.filter_by(student_id=current_user.id).order_by(AttendanceLog.date.desc()).all()
    attendance_logs_by_subject = {}
    for log in daily_logs:
        if log.subject not in attendance_logs_by_subject:
            attendance_logs_by_subject[log.subject] = []
        attendance_logs_by_subject[log.subject].append({
            'date': log.date,
            'status': log.status,
            'slots': log.slots
        })

    return render_template('student_dashboard.html', 
                          profile=profile,
                          attendance=attendance_records,
                          attendance_logs=attendance_logs_by_subject,
                          records=decrypted_records,
                          subject_summary=subject_summary,
                          grand_total=grand_total,
                          risk_att=r_att,
                          risk_marks=r_marks,
                          factors=factors)

@student_bp.route('/edit_profile', methods=['GET', 'POST'])
@login_required
@role_required('student')
def edit_profile():
    profile = StudentProfile.query.filter_by(user_id=current_user.id).first()
    
    if request.method == 'POST':
        profile.full_name = request.form.get('full_name')
        profile.email = request.form.get('email')
        profile.contact = request.form.get('contact')
        profile.dob = request.form.get('dob')
        profile.blood_group = request.form.get('blood_group')
        # Roll No usually isn't editable by student, but we can allow if asked
        profile.roll_no = request.form.get('roll_no')
        
        # Profile Pic (Simulation)
        # In real app: save file to static/uploads
        # Here we just take a URL or filename input for simplicity if text, or ignore
        
        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('student.dashboard'))
        
    return render_template('edit_profile.html', profile=profile)

@student_bp.route('/export_my_report')
@login_required
@role_required('student')
def export_my_report():
    import csv
    import io
    from flask import make_response
    
    # Fetch Data
    profile = StudentProfile.query.filter_by(user_id=current_user.id).first()
    attendance_records = Attendance.query.filter_by(student_id=current_user.id).all()
    records = AcademicRecord.query.filter_by(student_id=current_user.id).all()
    
    si = io.StringIO()
    cw = csv.writer(si)
    
    # Headers
    cw.writerow(['Report for', profile.full_name if profile else current_user.username])
    cw.writerow(['Roll No', profile.roll_no if profile else 'N/A'])
    cw.writerow(['Section', profile.section if profile and profile.section else 'N/A'])
    cw.writerow([])
    
    # Section 1: Attendance
    cw.writerow(['--- ATTENDANCE ---'])
    cw.writerow(['Subject', 'Classes Conducted', 'Classes Attended', 'Percentage'])
    for att in attendance_records:
        cw.writerow([att.subject, att.classes_conducted, att.classes_attended, f"{att.percentage}%"])
    cw.writerow([])
        
    # Section 2: Internal Marks
    cw.writerow(['--- ACADEMIC RECORDS ---'])
    cw.writerow(['Subject', 'Assignments', 'Evaluations', 'Remarks'])
    for rec in records:
        try:
            # Simple decryption simulation or direct access if verified
            marks_val = decrypt_data(rec.marks_encrypted)
        except:
            marks_val = "Error"
            
        cw.writerow([rec.subject, rec.assignments, rec.evaluations, rec.remarks])
        
    output = make_response(si.getvalue())
    output.headers["Content-Disposition"] = "attachment; filename=my_risk_report.csv"
    output.headers["Content-type"] = "text/csv"
    return output

@student_bp.route('/export_encoded_profile')
@login_required
@role_required('student')
def export_encoded_profile():
    import json
    from flask import make_response
    
    # 1. Fetch Data
    profile = StudentProfile.query.filter_by(user_id=current_user.id).first()
    
    if not profile:
        flash("Profile not found.", "error")
        return redirect(url_for('student.dashboard'))
        
    # 2. Serialize to Dictionary
    data = {
        "full_name": profile.full_name,
        "roll_no": profile.roll_no,
        "email": profile.email,
        "contact": profile.contact,
        "course": profile.course,
        "cgpa": profile.cgpa,
        "risk_status": {
            "attendance": profile.risk_attendance,
            "marks": profile.risk_marks
        },
        "generated_at": str(datetime.utcnow())
    }
    
    # 3. Convert to JSON String
    json_data = json.dumps(data, indent=4)
    
    # 4. Encode to Base64
    encoded_data = encode_base64(json_data)
    
    # 5. Return as Download
    response = make_response(encoded_data)
    response.headers["Content-Disposition"] = "attachment; filename=student_profile_encoded.txt"
    response.headers["Content-Type"] = "text/plain"
    
    return response
