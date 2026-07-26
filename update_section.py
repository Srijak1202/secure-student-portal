from app import create_app
from models import db, StudentProfile

app = create_app()

with app.app_context():
    print("Updating 'John Doe' Section to 'A'...")
    student = StudentProfile.query.filter_by(full_name="John Doe").first()
    if student:
        student.section = "A"
        db.session.commit()
        print("Updated successfully.")
    else:
        print("Student not found.")
