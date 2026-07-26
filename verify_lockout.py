from app import create_app
from models import User, db
from datetime import datetime

app = create_app()

def test_account_lockout():
    with app.app_context():
        # Clean up any previous test user
        user = User.query.filter_by(username='lockout_test').first()
        if user:
            db.session.delete(user)
            db.session.commit()
            
        # Create test user
        from utils.auth import hash_password
        test_user = User(username='lockout_test', password_hash=hash_password('password'), role='student', email='test@example.com')
        db.session.add(test_user)
        db.session.commit()
        
        print(f"Created test user: {test_user.username}")
        
        # Simulate 5 failed attempts
        for i in range(1, 6):
            print(f"Simulating failed attempt {i}...")
            # We are manually updating state because calling the route is complex without a full client
            # But we want to test the LOGIC helpers if possible, but here we tested route logic directly.
            # So let's mock the route behavior or better, use the test client.
            pass

    # Using test client to hit the route
    with app.test_client() as client:
        # 1. First attempt (fail)
        for i in range(1, 6):
            response = client.post('/login', data={
                'username': 'lockout_test',
                'password': 'wrong_password',
                'email': 'test@example.com' # Email doesn't matter for password fail check first usually, but in our logic password check is first
            }, follow_redirects=True)
            
            # Check DB state
            with app.app_context():
                u = User.query.filter_by(username='lockout_test').first()
                print(f"Attempt {i}: Failed attempts = {u.failed_login_attempts}")
                if i == 5:
                    assert u.lockout_until is not None
                    print("SUCCESS: Account locked after 5th attempt.")
                    
        # 2. 6th attempt (fail due to lockout)
        response = client.post('/login', data={
            'username': 'lockout_test',
            'password': 'password', # Correct password!
            'email': 'test@example.com'
        }, follow_redirects=True)
        
        assert b'Account is locked' in response.data or b'Account locked' in response.data
        print("SUCCESS: Login blocked during lockout period.")
        
        # Cleanup
        with app.app_context():
            u = User.query.filter_by(username='lockout_test').first()
            db.session.delete(u)
            db.session.commit()

if __name__ == "__main__":
    try:
        test_account_lockout()
        print("ALL TESTS PASSED.")
    except Exception as e:
        print(f"TEST FAILED: {e}")
