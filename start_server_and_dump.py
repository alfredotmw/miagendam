import subprocess
import time
import requests
import sys
import os
import signal
import json
from auth.jwt import create_access_token

def main():
    # 1. Start Uvicorn
    print("Starting uvicorn...")
    # Using a different port to avoid conflicts just in case, e.g., 8001, but main.py might hardcode things? 
    # No, main.py is standard FastAPI.
    proc = subprocess.Popen([sys.executable, "-m", "uvicorn", "main:app", "--port", "8005"], 
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    try:
        # Wait for server to start
        print("Waiting for server to start...")
        for i in range(10):
            try:
                requests.get("http://127.0.0.1:8005/docs", timeout=1)
                print("Server is up!")
                break
            except:
                time.sleep(1)
        else:
            print("Server failed to start.")
            return

        # 2. Authenticate
        print("Generating token...")
        token = create_access_token(data={"sub": "admin", "role": "ADMIN"})
        
        # 3. Fetch Feed
        url = f"http://127.0.0.1:8005/radioterapia/feed?token={token}"
        print(f"Fetching: {url}")
        
        resp = requests.get(url)
        print(f"Status: {resp.status_code}")
        print(f"Content-Type: {resp.headers.get('content-type')}")
        
        if resp.status_code == 200:
            data = resp.json()
            print(f"Row count: {len(data)}")
            if data:
                print("--- SAMPLE RECORD ---")
                print(json.dumps(data[0], indent=2))
        else:
            print(f"Error: {resp.text}")

    finally:
        # 4. Cleanup
        print("Killing server...")
        proc.terminate()
        try:
            proc.wait(timeout=2)
        except subprocess.TimeoutExpired:
            proc.kill()

if __name__ == "__main__":
    main()
