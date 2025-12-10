import requests
from datetime import date, datetime, timedelta

BASE_URL = "http://127.0.0.1:8000"
USERNAME = "Alfredo"
PASSWORD = "1234"

def login():
    print("Logging in...")
    r = requests.post(f"{BASE_URL}/users/login", json={"username": USERNAME, "password": PASSWORD})
    if r.status_code == 200:
        token = r.json()["access_token"]
        print(f"Writing token to artifacts dir...", flush=True)
        try:
            with open(r"C:\Users\alfre\.gemini\antigravity\brain\96291f65-fff3-4120-b09f-d234bc38a0de\token.txt", "w") as f:
                f.write(token)
            print(f"TOKEN saved to artifacts/token.txt", flush=True)
        except Exception as e:
            print(f"Error writing token: {e}", flush=True)
        return token
    print(f"Login failed: {r.text}")
    return None

def create_turno(token):
    print("Creating turno...")
    headers = {"Authorization": f"Bearer {token}"}
    data = {
        "agenda_id": 1, # Dr. Romilio Monzón
        "paciente_id": 1, # Juan Pérez
        "fecha": str(date.today()),
        "hora": "10:00",
        "duracion_custom": 15,
        "practicas_ids": [1], # Consulta
        "medico_derivante_nombre": "Dr. Test"
    }
    # Need to check if practicas exist first, but assuming seed data is there.
    # Actually, let's just try.
    r = requests.post(f"{BASE_URL}/turnos/", json=data, headers=headers)
    if r.status_code == 200:
        t = r.json()
        print(f"Turno created: ID {t['id']}")
        return t['id']
    print(f"Create turno failed: {r.text}")
    return None

def test_update_status(token, turno_id):
    print(f"Testing update status for ID {turno_id}...")
    headers = {"Authorization": f"Bearer {token}"}
    r = requests.patch(f"{BASE_URL}/turnos/{turno_id}", json={"estado": "COMPLETADO"}, headers=headers)
    if r.status_code == 200:
        print("Update status: SUCCESS")
    else:
        print(f"Update status FAILED: {r.text}")

def test_reschedule(token, turno_id):
    print(f"Testing reschedule for ID {turno_id}...")
    headers = {"Authorization": f"Bearer {token}"}
    new_date = str(date.today() + timedelta(days=1))
    new_time = "11:00"
import requests
from datetime import date, datetime, timedelta

BASE_URL = "http://127.0.0.1:8000"
USERNAME = "Alfredo"
PASSWORD = "1234"

def login():
    print("Logging in...")
    r = requests.post(f"{BASE_URL}/users/login", json={"username": USERNAME, "password": PASSWORD})
    if r.status_code == 200:
        return r.json()["access_token"]
    print(f"Login failed: {r.text}")
    return None

def create_turno(token):
    print("Creating turno...")
    headers = {"Authorization": f"Bearer {token}"}
    data = {
        "agenda_id": 1, # Dr. Romilio Monzón
        "paciente_id": 1, # Juan Pérez
        "fecha": str(date.today()),
        "hora": "10:00",
        "duracion_custom": 15,
        "practicas_ids": [1], # Consulta
        "medico_derivante_nombre": "Dr. Test"
    }
    # Need to check if practicas exist first, but assuming seed data is there.
    # Actually, let's just try.
    r = requests.post(f"{BASE_URL}/turnos/", json=data, headers=headers)
    if r.status_code == 200:
        t = r.json()
        print(f"Turno created: ID {t['id']}")
        return t['id']
    print(f"Create turno failed: {r.text}")
    return None

def test_update_status(token, turno_id):
    print(f"Testing update status for ID {turno_id}...")
    headers = {"Authorization": f"Bearer {token}"}
    r = requests.patch(f"{BASE_URL}/turnos/{turno_id}", json={"estado": "COMPLETADO"}, headers=headers)
    if r.status_code == 200:
        print("Update status: SUCCESS")
    else:
        print(f"Update status FAILED: {r.text}")

def test_reschedule(token, turno_id):
    print(f"Testing reschedule for ID {turno_id}...")
    headers = {"Authorization": f"Bearer {token}"}
    new_date = str(date.today() + timedelta(days=1))
    new_time = "11:00"
    r = requests.patch(f"{BASE_URL}/turnos/{turno_id}", json={"fecha": new_date, "hora": new_time}, headers=headers)
    if r.status_code == 200:
        print("Reschedule: SUCCESS")
    else:
        print(f"Reschedule FAILED: {r.text}")

if __name__ == "__main__":
    token = login()
    if token:
        # List Agendas
        print("\n📋 Listando Agendas...")
        headers = {"Authorization": f"Bearer {token}"}
        r = requests.get(f"{BASE_URL}/agendas/", headers=headers)
        if r.status_code == 200:
            agendas = r.json()
            for a in agendas:
                print(f"ID: {a['id']}, Nombre: {a['nombre']}, Tipo: {a['tipo']}")
        else:
            print(f"❌ Error listando agendas: {r.status_code}")

        tid = create_turno(token)
        if tid:
            test_update_status(token, tid)
            # Create another one for reschedule
            tid2 = create_turno(token)
            if tid2:
                test_reschedule(token, tid2)
        
        # Create a persistent turno for UI testing (Reschedule)
        print("Creating persistent turno for Reschedule testing...")
        headers = {"Authorization": f"Bearer {token}"}
        data = {
            "agenda_id": 1, 
            "paciente_id": 1,
            "fecha": str(date.today()),
            "hora": "13:00",
            "duracion_custom": 15,
            "practicas_ids": [1], 
            "medico_derivante_nombre": "Dr. Reschedule Test"
        }
        requests.post(f"{BASE_URL}/turnos/", json=data, headers=headers)

        # Check Slots
        print("\n🔍 Verificando Slots para Agenda 1, Hoy...")
        print("\n🔍 Verificando Slots para Agenda 1, Hoy...")
        today = str(date.today())
        r = requests.get(f"{BASE_URL}/agendas/1/slots?fecha={today}", headers=headers)
        if r.status_code == 200:
            slots = r.json()
            occupied_slots = [s for s in slots if s['turno'] is not None]
            print(f"Total slots: {len(slots)}")
            print(f"Occupied slots: {len(occupied_slots)}")
            for s in occupied_slots:
                t = s['turno']
                print(f"  - {s['hora']}: {t['paciente']['nombre']} ({t['estado']})")
        else:
            print(f"❌ Error fetching slots: {r.text}")
