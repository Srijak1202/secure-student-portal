from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from models import db, User, AcademicRecord, StudentProfile, MentoringLog, Attendance, AttendanceLog
from utils.auth import role_required
from utils.crypto import encrypt_data, sign_data

faculty_bp = Blueprint('faculty', __name__)

@faculty_bp.route('/dashboard')
@login_required
@role_required('faculty')
def dashboard():
    # Fetch students with their profiles
    # In a real app, join query. Here, we iterate (lab scale).
    students = User.query.filter_by(role='student').all()
    
    student_data = []
    for s in students:
        profile = StudentProfile.query.filter_by(user_id=s.id).first()
        
        # Calculate derived risk for summary view
        risk = "Safe"
        risk_att = "Safe"
        risk_marks = "Safe"
        
        if profile:
            risk_att = profile.risk_attendance
            risk_marks = profile.risk_marks
            
            if risk_att == 'High' or risk_marks == 'High':
                risk = "High"
            elif risk_att == 'Medium' or risk_marks == 'Medium':
                risk = "Medium"
        else:
            risk = "Unknown"

        student_data.append({
            'id': s.id,
            'username': s.username,
            'full_name': profile.full_name if profile else "Unknown",
            'cgpa': profile.cgpa if profile else 0.0,
            'sgpa': profile.current_sgpa if profile else 0.0,
            'risk': risk,
            'risk_att': risk_att, # Pass individual risks
            'risk_marks': risk_marks,
            'profile_id': profile.id if profile else None
        })
        
    return render_template('faculty_dashboard.html', students=student_data)

@faculty_bp.route('/add_assignment', methods=['POST'])
@login_required
@role_required('faculty')
def add_assignment():
    student_id = request.form.get('student_id')
    subject = current_user.subject
    
    if not subject:
        flash('Error: No Subject Assigned.', 'error')
        return redirect(url_for('faculty.dashboard'))

    assign_no = request.form.get('assign_no')
    obt = request.form.get('obt')
    tot = request.form.get('tot')
    remarks = request.form.get('remarks')
    convert_to = request.form.get('convert_to')
    
    # Logic for Conversion
    marks_display = f"{obt}/{tot}"
    final_marks = float(obt)
    
    if convert_to and float(convert_to) > 0:
        converted_val = (float(obt) / float(tot)) * float(convert_to)
        converted_val = round(converted_val, 2)
        marks_display = f"{obt}/{tot} -> {converted_val}/{convert_to}"
        final_marks = converted_val
    
    # Store simplified format
    assignments = f"A{assign_no}: {marks_display}"
    
    # Encryption & Integrity
    marks_str = str(final_marks)
    enc_marks = encrypt_data(marks_str)
    enc_risk = encrypt_data("0")
    
    raw = f"{student_id}{subject}{marks_str}0"
    sig = sign_data(raw)
    
    record = AcademicRecord(
        student_id=student_id,
        subject=subject,
        assignments=assignments,
        remarks=remarks,
        marks_encrypted=enc_marks,
        risk_score_encrypted=enc_risk,
        signature=sig
    )
    db.session.add(record)
    
    # Trigger Risk Update
    from utils.risk_engine import update_student_risk
    update_student_risk(student_id)
    
    db.session.commit()
    flash('Assignment marks uploaded.', 'success')
    return redirect(url_for('faculty.dashboard'))

@faculty_bp.route('/add_evaluation', methods=['POST'])
@login_required
@role_required('faculty')
def add_evaluation():
    student_id = request.form.get('student_id')
    subject = current_user.subject
    
    if not subject:
        flash('Error: No Subject Assigned.', 'error')
        return redirect(url_for('faculty.dashboard'))

    eval_type = request.form.get('eval_type')
    obt = request.form.get('obt')
    tot = request.form.get('tot')
    remarks = request.form.get('remarks')
    convert_to = request.form.get('convert_to')
    
    # Logic for Conversion
    marks_display = f"{obt}/{tot}"
    final_marks = float(obt)
    
    if convert_to and float(convert_to) > 0:
        converted_val = (float(obt) / float(tot)) * float(convert_to)
        converted_val = round(converted_val, 2)
        marks_display = f"{obt}/{tot} -> {converted_val}/{convert_to}"
        final_marks = converted_val
    
    evaluations = f"{eval_type}: {marks_display}"
    
    marks_str = str(final_marks)
    enc_marks = encrypt_data(marks_str)
    enc_risk = encrypt_data("0")
    
    raw = f"{student_id}{subject}{marks_str}0"
    sig = sign_data(raw)
    
    record = AcademicRecord(
        student_id=student_id,
        subject=subject,
        evaluations=evaluations,
        remarks=remarks,
        marks_encrypted=enc_marks,
        risk_score_encrypted=enc_risk,
        signature=sig
    )
    db.session.add(record)
    
    from utils.risk_engine import update_student_risk
    update_student_risk(student_id)
    
    db.session.commit()
    flash('Evaluation marks uploaded.', 'success')
    return redirect(url_for('faculty.dashboard'))

@faculty_bp.route('/add_mentoring', methods=['POST'])
@login_required
@role_required('faculty')
def add_mentoring():
    student_id = request.form.get('student_id')
    issue = request.form.get('issue')
    action = request.form.get('action')
    
    log = MentoringLog(
        student_id=student_id,
        mentor_id=current_user.id,
        issue=issue,
        action_taken=action,
        status='Pending'
    )
    db.session.add(log)
    db.session.commit()
    
    flash('Mentoring session logged.', 'success')
    return redirect(url_for('faculty.dashboard'))

@faculty_bp.route('/update_attendance', methods=['POST'])
@login_required
@role_required('faculty')
def update_attendance():
    student_id = request.form.get('student_id')
    status = request.form.get('status')
    att_date = request.form.get('att_date')  # Date from form
    slots = int(request.form.get('slots', 1)) # Default 1 slot
    subject = current_user.subject
    
    # Convert student_id to int for consistent comparison
    try:
        student_id = int(student_id)
    except (ValueError, TypeError):
        flash('Invalid student selected.', 'error')
        return redirect(url_for('faculty.dashboard'))
    
    # Check if attendance was already marked for this date using AttendanceLog
    existing_log = AttendanceLog.query.filter_by(
        student_id=student_id, subject=subject, date=att_date
    ).first()
    print(f"[DEBUG] Checking duplicate: student_id={student_id}, subject={subject}, date={att_date}, found={existing_log}")
    if existing_log:
        flash(f"⚠️ Attendance already marked for {att_date}.", 'error')
        return redirect(url_for('faculty.dashboard'))
    
    # Create or Get Aggregate Record
    att_record = Attendance.query.filter_by(student_id=student_id, subject=subject).first()
    
    if not att_record:
        att_record = Attendance(
            student_id=student_id, 
            subject=subject, 
            percentage=0.0, 
            month="Current",
            classes_conducted=0,
            classes_attended=0
        )
        db.session.add(att_record)
    
    # Update Counters based on SLOTS
    att_record.classes_conducted += slots
    if status == 'Present':
        att_record.classes_attended += slots
    
    # Store the date to prevent duplicate marking
    att_record.last_marked_date = att_date
    
    # Log the daily attendance entry
    log_entry = AttendanceLog(
        student_id=student_id,
        subject=subject,
        date=att_date,
        status=status,
        slots=slots
    )
    db.session.add(log_entry)
        
    # Recalculate Percentage
    if att_record.classes_conducted > 0:
        pct = (att_record.classes_attended / att_record.classes_conducted) * 100
        att_record.percentage = round(pct, 2)
        
    db.session.commit()
    
    # Trigger Risk Update
    from utils.risk_engine import update_student_risk
    update_student_risk(student_id)
    
    flash(f"Attendance marked: {status} for {slots} slot(s).", 'success')
    return redirect(url_for('faculty.dashboard'))

@faculty_bp.route('/manage_marks', methods=['POST'])
@login_required
@role_required('faculty')
def manage_marks():
    student_id = request.form.get('student_id')
    
    # Re-fetch generic dashboard data
    students = User.query.filter_by(role='student').all()
    student_data = []
    for s in students:
        profile = StudentProfile.query.filter_by(user_id=s.id).first()
        risk = "Safe"
        risk_att = "Safe"
        risk_marks = "Safe"
        if profile:
            risk_att = profile.risk_attendance
            risk_marks = profile.risk_marks
            if risk_att == 'High' or risk_marks == 'High':
                risk = "High"
            elif risk_att == 'Medium' or risk_marks == 'Medium':
                risk = "Medium"
        else:
            risk = "Unknown"
            
        student_data.append({
            'id': s.id,
            'username': s.username,
            'full_name': profile.full_name if profile else "Unknown",
            'cgpa': profile.cgpa if profile else 0.0,
            'sgpa': profile.current_sgpa if profile else 0.0,
            'risk': risk,
            'risk_att': risk_att,
            'risk_marks': risk_marks,
            'profile_id': profile.id if profile else None
        })
        
    # Fetch Records for Editing
    records = []
    selected_student_name = "Unknown"
    
    if student_id:
        target_student = User.query.get(student_id)
        if target_student:
             selected_student_name = target_student.username
    
        records = AcademicRecord.query.filter_by(
            student_id=student_id,
            subject=current_user.subject
        ).all()
        
    return render_template('faculty_dashboard.html', 
                           students=student_data, 
                           edit_records=records,
                           selected_student_id=student_id,
                           selected_student_name=selected_student_name)

@faculty_bp.route('/edit_record', methods=['POST'])
@login_required
@role_required('faculty')
def edit_record_marks():
    record_id = request.form.get('record_id')
    
    record = AcademicRecord.query.get(record_id)
    if not record:
        flash('Record not found', 'error')
        return redirect(url_for('faculty.dashboard'))
        
    # Security Check: Ownership
    if record.subject != current_user.subject:
        flash('Unauthorized: You can only edit your own subject marks.', 'error')
        return redirect(url_for('faculty.dashboard'))
        
    # Get New Values
    obt = request.form.get('obt')
    tot = request.form.get('tot')
    convert_to = request.form.get('convert_to')
    
    try:
        # Conversion Logic (Same as Add)
        marks_display = f"{obt}/{tot}"
        final_marks = float(obt)
        
        if convert_to and float(convert_to) > 0:
            converted_val = (float(obt) / float(tot)) * float(convert_to)
            converted_val = round(converted_val, 2)
            marks_display = f"{obt}/{tot} -> {converted_val}/{convert_to}"
            final_marks = converted_val
            
        # Update Text Field (Assignments or Evaluations)
        # Simple heuristic: If record.assignments is not null, update that, else evaluations
        if record.assignments:
            # Preserve prefix A1: etc if we can, but simpler to just rewrite for now or ask user?
            # User request: "edit the marks already published"
            # To handle complexity, we will replace the content after the colon if possible, 
            # Or just replace the whole string if it's simple.
            # For this MVP: We assume the user wants to update the value. 
            # We will use a split approach if ':' exists.
            
            prefix = record.assignments.split(':')[0] if ':' in record.assignments else "Updated"
            record.assignments = f"{prefix}: {marks_display}"
            
        elif record.evaluations:
            prefix = record.evaluations.split(':')[0] if ':' in record.evaluations else "Updated"
            record.evaluations = f"{prefix}: {marks_display}"
            
        # Update Encrypted Data
        marks_str = str(final_marks)
        enc_marks = encrypt_data(marks_str)
        
        # We need to re-sign. Original raw format: student_id + subject + marks + risk
        # We need to decrypt risk first? Or just assume 0 or keep existing?
        # Ideally we'd decrypt check, but here we can just re-sign with current risk (which is usually reset to 0 or triggers re-calc)
        # For simplicity/consistency with Add routes:
        enc_risk = encrypt_data("0")
        
        raw = f"{record.student_id}{record.subject}{marks_str}0"
        sig = sign_data(raw)
        
        record.marks_encrypted = enc_marks
        record.risk_score_encrypted = enc_risk
        record.signature = sig
        
        db.session.commit()
        
        # Trigger Risk Update
        from utils.risk_engine import update_student_risk
        update_student_risk(record.student_id)
        
        flash('Marks updated successfully.', 'success')
        
    except ValueError:
        flash('Invalid input values.', 'error')

    # Return to Manage View (by simulating POST? or just Dashboard)
    # Redirecting to dashboard clears selection, which is fine for now.
    return redirect(url_for('faculty.dashboard'))

@faculty_bp.route('/export_subject_report')
@login_required
@role_required('faculty')
def export_subject_report():
    import csv
    import io
    from flask import make_response
    
    subject = current_user.subject
    # Get all students
    students = User.query.filter_by(role='student').all()
    
    si = io.StringIO()
    cw = csv.writer(si)
    cw.writerow([f'Risk Report for Subject: {subject}'])
    cw.writerow([])
    
    # Headers
    cw.writerow(['Roll No', 'Name', 'Section', 'Attendance %', 'Internal Marks (Assignments)', 'Internal Marks (Evaluations)', 'Risk (Att)', 'Risk (Marks)'])
    
    for s in students:
        profile = StudentProfile.query.filter_by(user_id=s.id).first()
        att = Attendance.query.filter_by(student_id=s.id, subject=subject).first()
        record = AcademicRecord.query.filter_by(student_id=s.id, subject=subject).first()
        
        row = [
            profile.roll_no if profile else 'N/A',
            profile.full_name if profile else s.username,
            profile.section if profile and profile.section else 'N/A',
            f"{att.percentage}%" if att else '0%',
            record.assignments if record else 'N/A',
            record.evaluations if record else 'N/A',
            profile.risk_attendance if profile else 'Unknown',
            profile.risk_marks if profile else 'Unknown'
        ]
        cw.writerow(row)
        
    output = make_response(si.getvalue())
    output.headers["Content-Disposition"] = f"attachment; filename={subject}_risk_report.csv"
    output.headers["Content-type"] = "text/csv"
    return output
