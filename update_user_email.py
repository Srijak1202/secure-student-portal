from app import create_app
from models import db, User

app = create_app()

with app.app_context():
    print("Updating 'John Doe' (User) Email to 'john@univ.edu'...")
    user = User.query.filter_by(username="CB.EN.U4CSE21001").first()
    if user:
        user.email = "john@univ.edu"
        db.session.commit()
        print("Updated user email successfully.")
    else:
        print("User not found.")
