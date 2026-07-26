from app import create_app
from models import User, db, StudentProfile
import base64
import json

app = create_app()

def test_encoding_export():
    with app.test_client() as client:
        with app.app_context():
            # Ensure student user exists and has a profile
            user = User.query.filter_by(username='student').first()
            if not user:
                print("Error: Default 'student' user not found. Run init_db.py first.")
                return

            profile = StudentProfile.query.filter_by(user_id=user.id).first()
            if not profile:
                print("Error: Student profile not found.")
                return
                
            print(f"Testing for user: {user.username}")
            
            # Login
            login_resp = client.post('/login', data={
                'username': 'student',
                'password': 'student123',
                'email': user.email if user.email else 'student@example.com' # Needs to match DB if MFA check exists
            }, follow_redirects=True)
            
            # We might be blocked by MFA or Lockout if we messed up previous tests or state.
            # Assuming happy path for now or bypassing login requirement if possible (but route is protected)
            # Actually, let's just cheat the login using Flask-Login's test_request_context capabilities or just trust the login post works if credentials are default.
            
            # Bypass MFA check in session if needed
            with client.session_transaction() as sess:
                sess['mfa_completed'] = True
                
            # Hit the route
            response = client.get('/student/export_encoded_profile')
            
            if response.status_code != 200:
                print(f"FAILED: Route returned {response.status_code}")
                if response.status_code == 302:
                     print(f"Redirected to: {response.location}")
                return
                
            content = response.data.decode('utf-8')
            print(f"Received Content (First 50 chars): {content[:50]}...")
            
            # Verify Base64
            try:
                decoded_bytes = base64.b64decode(content)
                decoded_str = decoded_bytes.decode('utf-8')
                data = json.loads(decoded_str)
                
                print("SUCCESS: Content is valid Base64.")
                print("Decoded JSON keys:", data.keys())
                
                if data['full_name'] == profile.full_name:
                     print("SUCCESS: Decoded data matches database.")
                else:
                     print("WARNING: Data mismatch.")
                     
            except Exception as e:
                print(f"FAILED to decode Base64: {e}")

if __name__ == "__main__":
    test_encoding_export()
