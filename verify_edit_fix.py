import requests
import json

BASE_URL = "http://localhost:8000"

def get_token():
    try:
        with open("token.txt", "r") as f:
            return f.read().strip()
    except FileNotFoundError:
        return None

TOKEN = get_token()
HEADERS = {"Authorization": f"Bearer {TOKEN}"}

def verify_correct_payload():
    print("\n--- Testing Correct Payload (With DNI) ---")
    
    # 1. Get a patient
    try:
        res = requests.get(f"{BASE_URL}/pacientes/", params={"limit": 1}, headers=HEADERS)
        if not res.ok:
            print(f"Failed to get patients: {res.text}")
            return
            
        patients = res.json()
        if not patients:
            print("No patients found.")
            return
            
        p = patients[0]
        pid = p['id']
        print(f"Targeting Patient ID: {pid}, Name: {p['nombre']}")
        
    except Exception as e:
        print(f"Error: {e}")
        return

    # 2. Send Payload WITH DNI (Simulating fixed frontend)
    payload = {
        "nombre": p['nombre'],
        "apellido": p['apellido'],
        "dni": p['dni'], # 👈 CORRECT: Includes DNI
        "fecha_nacimiento": p['fecha_nacimiento'],
        "telefono": p['telefono'],
        "obra_social_nombre": "OS_VERIFY_FIX"
    }
    
    print("Sending PUT request WITH DNI...")
    res = requests.put(f"{BASE_URL}/pacientes/{pid}", json=payload, headers=HEADERS)
    
    print(f"Status Code: {res.status_code}")
    print(f"Response Body: {res.text}")
    
    if res.status_code == 200:
        print("✅ VERIFICATION SUCCESS: Server accepted the payload.")
    else:
        print(f"❌ VERIFICATION FAILED: Got status {res.status_code}")

if __name__ == "__main__":
    verify_correct_payload()
