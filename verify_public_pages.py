from app import create_app

app = create_app()

def test_public_pages():
    with app.test_client() as client:
        # Test Access Control Page
        resp = client.get('/access_control')
        print(f"Access Control Page Status: {resp.status_code}")
        assert resp.status_code == 200, "Access control page should be public"

        # Test Encoding Theory Page
        resp = client.get('/encoding_theory')
        print(f"Encoding Theory Page Status: {resp.status_code}")
        assert resp.status_code == 200, "Encoding theory page should be public"
        
        if b"Security Levels & Risks" in resp.data:
            print("SUCCESS: Encoding theory content found.")
        else:
            print("FAILURE: Content mismatch.")

if __name__ == "__main__":
    test_public_pages()
