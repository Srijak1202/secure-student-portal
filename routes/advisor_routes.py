from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from models import db, User, StudentProfile
from utils.auth import role_required

advisor_bp = Blueprint('class_advisor', __name__)

@advisor_bp.route('/dashboard', methods=['GET', 'POST'])
@login_required
@role_required('class_advisor')
def dashboard():
    students = User.query.filter_by(role='student').all()
    selected_student = None
    profile = None
    
    if request.method == 'POST':
        student_id = request.form.get('student_id')
        if student_id:
            selected_student = User.query.get(student_id)
            if selected_student:
                profile = StudentProfile.query.filter_by(user_id=selected_student.id).first()
                if not profile:
                    flash('Student Profile not initialized yet.', 'warning')
                    
    # Prepare list for datalist
    student_opts = []
    for s in students:
        s_prof = StudentProfile.query.filter_by(user_id=s.id).first()
        full_name = s_prof.full_name if s_prof else "Unknown"
        student_opts.append({'id': s.id, 'username': s.username, 'full_name': full_name})

    return render_template('class_advisor_dashboard.html', 
                           students=student_opts, 
                           selected_student=selected_student,
                           profile=profile)

@advisor_bp.route('/update_metrics', methods=['POST'])
@login_required
@role_required('class_advisor')
def update_metrics():
    student_id = request.form.get('student_id')
    cgpa = request.form.get('cgpa')
    sgpa = request.form.get('sgpa') # Float input
    grace = request.form.get('grace_marks')
    remarks = request.form.get('advisor_remarks')
    
    profile = StudentProfile.query.filter_by(user_id=student_id).first()
    if not profile:
        flash('Profile not found', 'error')
        return redirect(url_for('class_advisor.dashboard'))
        
    try:
        if cgpa: profile.cgpa = float(cgpa)
        if sgpa and sgpa != 'Nil':
            profile.current_sgpa = float(sgpa)
        elif sgpa == 'Nil':
            profile.current_sgpa = None
        if grace: profile.grace_marks = float(grace)
        if remarks: profile.advisor_remarks = remarks
        
        db.session.commit()
        flash(f"Metrics updated for {profile.full_name}", 'success')
    except ValueError:
        flash("Invalid numerical input for CGPA/SGPA/Grace Marks", 'error')
        
    # Redirect back to search (could improve UX to keep selection, but simple redirect for now)
    return redirect(url_for('class_advisor.dashboard'))

@advisor_bp.route('/export_class_report')
@login_required
@role_required('class_advisor')
def export_class_report():
    import csv
    import io
    from flask import make_response
    
    # Advisor can see all or we filter if we had advisor section. 
    # For now, exporting all students sorted by Section.
    
    students = User.query.filter_by(role='student').all()
    
    si = io.StringIO()
    cw = csv.writer(si)
    cw.writerow(['Class Advisor Risk Report - All Sections'])
    cw.writerow([])
    
    cw.writerow(['Section', 'Roll No', 'Name', 'Overview Risk (Att)', 'Overview Risk (Marks)', 'CGPA', 'Advisor Remarks'])
    
    # Sort by section (simple sort in Python since SQL sort might need join)
    student_list = []
    for s in students:
        profile = StudentProfile.query.filter_by(user_id=s.id).first()
        student_list.append({
            'section': profile.section if profile and profile.section else 'Z-NoSection',
            'roll': profile.roll_no if profile else 'N/A',
            'name': profile.full_name if profile else s.username,
            'r_att': profile.risk_attendance if profile else 'Unknown',
            'r_mrk': profile.risk_marks if profile else 'Unknown',
            'cgpa': profile.cgpa if profile else 0.0,
            'remarks': profile.advisor_remarks if profile else ''
        })
        
    # Sort
    student_list.sort(key=lambda x: (x['section'], x['roll']))
    
    for s in student_list:
        cw.writerow([s['section'], s['roll'], s['name'], s['r_att'], s['r_mrk'], s['cgpa'], s['remarks']])
        
    output = make_response(si.getvalue())
    output.headers["Content-Disposition"] = "attachment; filename=class_risk_report.csv"
    output.headers["Content-type"] = "text/csv"
    return output
