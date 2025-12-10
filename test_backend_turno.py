
import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8000"

def test_flow():
    # 1. Login
    print("🔑 Logging in...")
    try:
        resp = requests.post(f"{BASE_URL}/users/login", json={"username": "Alfredo", "password": "1234"})
        if resp.status_code != 200:
            print(f"❌ Login failed: {resp.text}")
            return
        token = resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        print("✅ Login successful")
    except Exception as e:
        print(f"❌ Connection error: {e}")
        return

    # 2. Get Agenda (we need one)
    print("📅 Fetching agendas...")
    resp = requests.get(f"{BASE_URL}/agendas/", headers=headers)
    agendas = resp.json()
    if not agendas:
        print("❌ No agendas found")
        return
    agenda_id = agendas[0]["id"]
    agenda_tipo = agendas[0]["tipo"]
    print(f"✅ Using Agenda ID: {agenda_id} ({agenda_tipo})")

    # 3. Get Practica
    print("🩺 Fetching practicas...")
    resp = requests.get(f"{BASE_URL}/practicas/", headers=headers)
    practicas = resp.json()
    # Filter by agenda type if possible, or just pick one
    practica_id = practicas[0]["id"]
    print(f"✅ Using Practica ID: {practica_id}")

    # 4. Create/Find Patient
    print("👤 Creating patient...")
    dni = 99999999
    resp = requests.get(f"{BASE_URL}/pacientes/dni/{dni}", headers=headers)
    if resp.status_code == 200:
        paciente_id = resp.json()["id"]
        print(f"✅ Patient found: {paciente_id}")
    else:
        # Create
        paciente_data = {
            "dni": str(dni),
            "nombre": "TEST",
            "apellido": "API",
            "fecha_nacimiento": "1990-01-01",
            "sexo": "M",
            "telefono": "123456",
            "obra_social_nombre": "PARTICULAR"
        }
        resp = requests.post(f"{BASE_URL}/pacientes/", json=paciente_data, headers=headers)
        if resp.status_code != 200:
            print(f"❌ Failed to create patient: {resp.text}")
            return
        paciente_id = resp.json()["id"]
        print(f"✅ Patient created: {paciente_id}")

    # 5. Create Turno
    print("📝 Creating Turno...")
    turno_data = {
        "paciente_id": paciente_id,
        "agenda_id": agenda_id,
        "fecha": datetime.now().strftime("%Y-%m-%d"),
        "hora": "12:00:00",
        "practicas_ids": [practica_id],
        "medico_derivante_nombre": "DR. TEST API",
        "patologia": "TEST"
    }
    
    print(f"Payload: {json.dumps(turno_data, indent=2)}")
    
    resp = requests.post(f"{BASE_URL}/turnos/", json=turno_data, headers=headers)
    
    if resp.status_code == 200:
        print("✅ SUCCESS: Turno created!")
        print(resp.json())
    else:
        print(f"❌ FAILED: {resp.status_code}")
        print(resp.text)

if __name__ == "__main__":
    test_flow()
