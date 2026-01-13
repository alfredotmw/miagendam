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

def test_missing_dni_update():
    print("\n--- Testing Missing DNI Update (Reproduction) ---")
    
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

    # 2. Send Payload SIMILAR to what Frontend sends (Missing DNI)
    # Frontend sends: nombre, apellido, fecha_nacimiento, telefono, obra_social_nombre, medico_derivante_nombre
    payload = {
        "nombre": p['nombre'],
        "apellido": p['apellido'],
        "fecha_nacimiento": p['fecha_nacimiento'],
        "telefono": p['telefono'],
        # "dni": p['dni']  <-- MISSING DNI
    }
    
    print("Sending PUT request WITHOUT DNI...")
    res = requests.put(f"{BASE_URL}/pacientes/{pid}", json=payload, headers=HEADERS)
    
    print(f"Status Code: {res.status_code}")
    print(f"Response Body: {res.text}")
    
    if res.status_code == 422:
        print("✅ REPRODUCTION SUCCESS: Server returned 422 Unprocessable Entity (Validation Error).")
    else:
        print(f"❌ REPRODUCTION FAILED: Got status {res.status_code}")

if __name__ == "__main__":
    test_missing_dni_update()
