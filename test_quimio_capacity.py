import requests
from datetime import date, datetime, timedelta

BASE_URL = "http://127.0.0.1:8000"
USERNAME = "Alfredo"
PASSWORD = "1234"

def get_token():
    response = requests.post(
        f"{BASE_URL}/token",
        data={"username": USERNAME, "password": PASSWORD}
    )
    if response.status_code == 200:
        return response.json()["access_token"]
    else:
        print("Error obteniendo token:", response.text)
        return None

def test_quimio_capacity():
    token = get_token()
    if not token:
        return

    headers = {"Authorization": f"Bearer {token}"}

    # 1. Find Quimioterapia Agenda
    print("🔍 Buscando agenda de Quimioterapia...")
    agendas = requests.get(f"{BASE_URL}/agendas/", headers=headers).json()
    quimio_agenda = next((a for a in agendas if a["tipo"] == "QUIMIOTERAPIA"), None)

    if not quimio_agenda:
        print("❌ No se encontró agenda de Quimioterapia")
        return

    print(f"✅ Agenda encontrada: {quimio_agenda['nombre']} (ID: {quimio_agenda['id']})")

    # 2. Define test date and time
    test_date = (date.today() + timedelta(days=1)).isoformat()
    test_time = "10:00"
    print(f"📅 Fecha de prueba: {test_date} {test_time}")

    # 3. Create 3 appointments
    print("📝 Creando 3 turnos para la misma hora...")
    for i in range(3):
        turno_data = {
            "agenda_id": quimio_agenda["id"],
            "fecha": test_date,
            "hora": test_time,
            "paciente_id": 1, # Assuming patient ID 1 exists
            "practica_id": 1 # Assuming practice ID 1 exists (dummy)
        }
        # We need to find a valid practice for Quimioterapia ideally, but let's try generic
        # Actually, let's just use the first practice available or hardcode if we know IDs
        # For simplicity, let's try to get a valid practice ID first
        if i == 0:
             practicas = requests.get(f"{BASE_URL}/practicas/?categoria=QUIMIOTERAPIA", headers=headers).json()
             if practicas:
                 turno_data["practica_id"] = practicas[0]["id"]
             else:
                 print("⚠️ No se encontraron prácticas de Quimioterapia, usando ID 1 genérico")
        
        # Note: The backend might block overlapping appointments if we didn't update the CREATE logic?
        # Wait, the create logic usually checks for availability. 
        # If the create logic checks `get_agenda_slots` or similar, it might pass now.
        # But if it has its own overlap check, we might fail here.
        # Let's see.
        
        resp = requests.post(f"{BASE_URL}/turnos/", json=turno_data, headers=headers)
        if resp.status_code == 200:
            print(f"   ✅ Turno {i+1} creado (ID: {resp.json()['id']})")
        else:
            print(f"   ❌ Error creando turno {i+1}: {resp.text}")

    # 4. Fetch slots
    print("📥 Obteniendo slots...")
    slots_resp = requests.get(f"{BASE_URL}/agendas/{quimio_agenda['id']}/slots?fecha={test_date}", headers=headers)
    slots = slots_resp.json()

    # 5. Verify 10:00 AM slots
    slots_10am = [s for s in slots if s["hora"] == "10:00"]
    print(f"📊 Slots encontrados a las 10:00: {len(slots_10am)}")

    if len(slots_10am) == 7:
        print("   ✅ Correcto: Se generaron 7 slots.")
    else:
        print(f"   ❌ Incorrecto: Se esperaban 7 slots, se encontraron {len(slots_10am)}.")

    occupied = [s for s in slots_10am if not s["disponible"]]
    available = [s for s in slots_10am if s["disponible"]]

    print(f"   🔒 Ocupados: {len(occupied)}")
    print(f"   🔓 Disponibles: {len(available)}")

    if len(occupied) >= 3: # Might be more if we ran test multiple times
        print("   ✅ Correcto: Al menos 3 slots ocupados.")
    else:
        print("   ❌ Incorrecto: Menos de 3 slots ocupados.")

if __name__ == "__main__":
    test_quimio_capacity()
