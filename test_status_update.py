import requests
import sys

BASE_URL = "http://127.0.0.1:8000"

# 1. Login
print("Logging in...")
r = requests.post(f"{BASE_URL}/users/login", json={"username": "Alfredo", "password": "1234"})
if r.status_code != 200:
    print(f"Login failed: {r.text}")
    sys.exit(1)
token = r.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

# 2. Get an agenda
print("Getting agendas...")
r = requests.get(f"{BASE_URL}/agendas/", headers=headers)
agendas = r.json()
if not agendas:
    print("No agendas found")
    sys.exit(1)
agenda_id = agendas[0]["id"]

# 3. Create a turno
print("Creating turno...")
turno_data = {
    "fecha": "2025-12-05T09:00:00",
    "hora": "09:00",
    "paciente_id": 1, # Assuming patient 1 exists
    "agenda_id": agenda_id,
    "practicas_ids": [1], # Assuming practice 1 exists
    "medico_derivante_nombre": "TEST MEDICO"
}
r = requests.post(f"{BASE_URL}/turnos/", json=turno_data, headers=headers)
if r.status_code not in [200, 201]:
    # If fails, maybe patient doesn't exist, try to find one
    print(f"Create failed: {r.text}. Trying to find a patient...")
    # ... (skip complexity, just assume it works or fail)
    sys.exit(1)

turno = r.json()
turno_id = turno["id"]
print(f"Turno created: ID {turno_id}, Status: {turno['estado']}")

# 4. Update status to COMPLETADO
print(f"Updating status of turno {turno_id} to COMPLETADO...")
r = requests.patch(f"{BASE_URL}/turnos/{turno_id}", json={"estado": "COMPLETADO"}, headers=headers)
if r.status_code != 200:
    print(f"Update failed: {r.text}")
    sys.exit(1)

updated_turno = r.json()
print(f"Update response status: {updated_turno['estado']}")

# 5. Fetch again to verify persistence
print("Fetching turno again...")
# We don't have a direct get_turno endpoint exposed in the router snippet I saw, 
# but we can check via agenda slots or just trust the patch response if it returned the object.
# Let's try to list turnos
r = requests.get(f"{BASE_URL}/turnos/?agenda_id={agenda_id}&limit=500", headers=headers)
turnos = r.json()
found = False
for t in turnos:
    if t["id"] == turno_id:
        print(f"Found turno in list. Status: {t['estado']}")
        if t["estado"] == "COMPLETADO":
            print("SUCCESS: Status is COMPLETADO")
        else:
            print(f"FAILURE: Status is {t['estado']}")
        found = True
        break

if not found:
    print("Turno not found in list")
