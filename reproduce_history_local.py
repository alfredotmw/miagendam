import requests
import subprocess
import sys
import time
import os
from auth.jwt import create_access_token
from database import SessionLocal
from models.paciente import Paciente

def main():
    # 1. Start Server
    print("Starting server...")
    proc = subprocess.Popen([sys.executable, "-m", "uvicorn", "main:app", "--port", "8006"], 
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    try:
        # Wait for server
        for i in range(10):
            try:
                requests.get("http://127.0.0.1:8006/docs", timeout=1)
                print("Server UP")
                break
            except:
                time.sleep(1)
        else:
            print("Server failed to start")
            return

        # 2. Find a Patient
        db = SessionLocal()
        pat = db.query(Paciente).first()
        db.close()
        
        if not pat:
            print("No patients in DB")
            return
            
        print(f"Testing with Patient: {pat.dni}")
        
        # 3. Request
        token = create_access_token(data={"sub": "admin", "role": "ADMIN"})
        url = f"http://127.0.0.1:8006/historia-clinica/dni/{pat.dni}/timeline"
        
        print(f"GET {url}")
        resp = requests.get(url, headers={"Authorization": f"Bearer {token}"})
        
        print(f"Status: {resp.status_code}")
        if resp.status_code != 200:
            print(resp.text)
        else:
            print("Success!")
            data = resp.json()
            print(f"Events: {len(data['timeline'])}")

    finally:
        proc.terminate()
        try:
            proc.wait(timeout=2)
        except:
            proc.kill()

if __name__ == "__main__":
    main()
