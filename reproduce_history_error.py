from fastapi.testclient import TestClient
from main import app
from auth.jwt import create_access_token 
import json
import sys
import os

client = TestClient(app)

def test_history():
    print("Generating token...")
    token = create_access_token(data={"sub": "admin", "role": "ADMIN"})
    
    # 1. Get a patient ID or DNI first
    # We can try to create one or list one.
    # Let's try to query patients
    print("Searching for a patient...")
    resp = client.get(f"/pacientes/?limit=1", headers={"Authorization": f"Bearer {token}"})
    if resp.status_code != 200:
        print(f"Failed to list patients: {resp.status_code} {resp.text}")
        return

    patients = resp.json()
    if not patients:
        print("No patients found in DB. Cannot test history.")
        return

    p = patients[0]
    dni = p['dni']
    print(f"Testing history for Patient DNI: {dni} ({p['apellido']})")
    
    url = f"/historia-clinica/dni/{dni}/timeline"
    print(f"Requesting: {url}")
    
    try:
        response = client.get(url, headers={"Authorization": f"Bearer {token}"})
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("--- SUCCESS ---")
            print(f"Timeline events: {len(data.get('timeline', []))}")
            # Check for patologia in events
            for ev in data['timeline']:
                if ev['tipo'] == 'TURNO':
                    sc = ev.get('structured_content', {})
                    pat = sc.get('patologia')
                    if pat:
                        print(f"Turno with patologia found: {pat}")
                    else:
                        print(f"Turno without patologia in structured_content (OK if None)")
        else:
            print("--- ERROR ---")
            print(response.text)
            
    except Exception as e:
        print(f"Exception calling client: {e}")

if __name__ == "__main__":
    test_history()
