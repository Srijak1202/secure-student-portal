from models import db, StudentProfile, Attendance, RiskThreshold, AcademicRecord
from utils.crypto import decrypt_data

def calculate_split_risk(student_id):
    """
    Returns separate risk levels for Attendance and Marks.
    Satisfies Requirement: Split Risk Analysis
    """
    risk_att = "Safe"
    risk_marks = "Safe"
    factors_att = []
    factors_marks = []
    
    # 1. Fetch Thresholds
    min_att = RiskThreshold.query.filter_by(metric_name='min_attendance').first() # 75%
    crit_att = RiskThreshold.query.filter_by(metric_name='critical_attendance').first() # 65%
    
    thresholds = {
        'min_att': min_att.value if min_att else 75.0,
        'crit_att': crit_att.value if crit_att else 65.0,
    }
    
    # 2. Check Attendance
    attendances = Attendance.query.filter_by(student_id=student_id).all()
    if attendances:
        avg_att = sum([a.percentage for a in attendances]) / len(attendances)
        if avg_att < thresholds['crit_att']:
            risk_att = "High"
            factors_att.append(f"Critical Avg Attendance ({avg_att:.1f}%)")
        elif avg_att < thresholds['min_att']:
            risk_att = "Medium"
            factors_att.append(f"Low Avg Attendance ({avg_att:.1f}%)")
            
    # 3. Check Marks (Percentage-based)
    records = AcademicRecord.query.filter_by(student_id=student_id).all()
    subject_marks = {}  # subject -> list of (obtained, total)
    
    for rec in records:
        subj = rec.subject
        if subj not in subject_marks:
            subject_marks[subj] = {'obtained': 0, 'total': 0}
        
        # Try to parse obtained/total from assignments or evaluations text
        text = rec.assignments or rec.evaluations or ""
        parsed = False
        
        # Parse format like "A1: 8/10" or "A1: 8/10 -> 4.0/5"
        if '/' in text:
            try:
                # Get the part after ':'
                val_part = text.split(':')[-1].strip()
                # If there's a conversion arrow, use the converted values
                if '->' in val_part:
                    converted = val_part.split('->')[-1].strip()
                    parts = converted.split('/')
                    obt = float(parts[0].strip())
                    tot = float(parts[1].strip())
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
        
        # Fallback: use decrypted marks as a score out of 100
        if not parsed:
            try:
                marks = float(decrypt_data(rec.marks_encrypted))
                subject_marks[subj]['obtained'] += marks
                subject_marks[subj]['total'] += 100
            except:
                continue
    
    # Calculate average percentage across all subjects
    if subject_marks:
        subject_percentages = []
        for subj, vals in subject_marks.items():
            if vals['total'] > 0:
                pct = (vals['obtained'] / vals['total']) * 100
                subject_percentages.append(pct)
        
        if subject_percentages:
            avg_marks_pct = sum(subject_percentages) / len(subject_percentages)
            
            if avg_marks_pct < 40:
                risk_marks = "High"
                factors_marks.append(f"Critical Avg Marks ({avg_marks_pct:.1f}%)")
            elif avg_marks_pct < 70:
                risk_marks = "Medium"
                factors_marks.append(f"Low Avg Marks ({avg_marks_pct:.1f}%)")
        
    return risk_att, risk_marks, factors_att, factors_marks

def update_student_risk(student_id):
    """
    Updates the StudentProfile with the calculated risks.
    """
    r_att, r_marks, f_att, f_marks = calculate_split_risk(student_id)
    profile = StudentProfile.query.filter_by(user_id=student_id).first()
    if profile:
        profile.risk_attendance = r_att
        profile.risk_marks = r_marks
        db.session.commit()
    return r_att, r_marks, f_att + f_marks
