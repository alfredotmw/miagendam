import requests
import json
import sys
from auth.jwt import create_access_token

def main():
    print("Generating token...")
    token = create_access_token(data={"sub": "admin", "role": "ADMIN"})
    
    url = f"http://127.0.0.1:8005/radioterapia/feed?token={token}"
    print(f"Fetching: {url}")
    
    try:
        resp = requests.get(url, timeout=5)
        print(f"Status: {resp.status_code}")
        print(f"Content-Type: {resp.headers.get('content-type')}")
        
        if resp.status_code == 200:
            data = resp.json()
            print(f"Row count: {len(data)}")
            if data:
                print("--- SAMPLE RECORD ---")
                print(json.dumps(data[0], indent=2))
                
                print("\n--- TYPES ---")
                for k,v in data[0].items():
                    print(f"{k}: {type(v).__name__} ({v})")
            else:
                print("No records found.")
        else:
            print(f"Error: {resp.text}")
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    main()
