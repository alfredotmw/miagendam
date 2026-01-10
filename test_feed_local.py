
from fastapi.testclient import TestClient
from main import app
from auth.jwt import create_access_token

def test_feed_endpoint():
    client = TestClient(app)
    
    # Generate a valid token
    token = create_access_token({"sub": "admin", "role": "ADMIN"})
    
    # Call the endpoint
    print(f"Testing GET /radioterapia/feed with token...")
    response = client.get(f"/radioterapia/feed?token={token}")
    
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Success! Retrieved {len(data)} records.")
        if len(data) > 0:
            print("Sample record:", data[0])
    else:
        print("Error response:", response.text)

if __name__ == "__main__":
    test_feed_endpoint()
