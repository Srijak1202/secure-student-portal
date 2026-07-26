from app import create_app
from models import db, StudentProfile

app = create_app()

with app.app_context():
    print("Checking StudentProfile data...")
    profiles = StudentProfile.query.all()
    print(f"Total Profiles: {len(profiles)}")
    
    at_risk = 0
    for p in profiles:
        print(f"User: {p.full_name}, Risk Att: '{p.risk_attendance}', Risk Marks: '{p.risk_marks}'")
        if p.risk_attendance != 'Safe' or p.risk_marks != 'Safe':
            at_risk += 1
            
    print(f"\nTotal At-Risk Students Found: {at_risk}")
