from fastapi.testclient import TestClient
from main import app
from auth.jwt import create_access_token 
import json
import sys
import os

# Add parent directory to path if needed (though running from root usually works)
sys.path.append(os.getcwd())

client = TestClient(app)

def dump_feed():
    # Generate a fresh token
    print("Generating token...")
    token = create_access_token(data={"sub": "admin", "role": "ADMIN"})
    
    url = f"/radioterapia/feed?token={token}"
    print(f"Requesting: {url}")
    
    response = client.get(url)
    
    print(f"Status Code: {response.status_code}")
    print(f"Content-Type: {response.headers.get('content-type')}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"Total items: {len(data)}")
        if len(data) > 0:
            print("--- JSON OUTPUT SAMPLE (First 1 items) ---")
            print(json.dumps(data[:1], indent=2, default=str)) # Use default=str for any dates
            
            # Detailed type check
            print("\n--- TYPE ANALYSIS ---")
            item = data[0]
            for k, v in item.items():
                print(f"Key: {k}, Type: {type(v).__name__}, Value: {v}")
        else:
            print("No data returned.")
    else:
        print("Error response:")
        print(response.text)

if __name__ == "__main__":
    dump_feed()
