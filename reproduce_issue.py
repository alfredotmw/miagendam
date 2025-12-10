import requests
import json
from datetime import datetime

BASE_URL = "http://127.0.0.1:8000"

def login():
    print("Logging in...")
    response = requests.post(f"{BASE_URL}/users/login", json={"username": "Alfredo", "password": "1234"})
    if response.status_code == 200:
        print("Login successful")
        return response.json()["access_token"]
    else:
        print(f"Login failed: {response.text}")
        return None

def get_agendas(token):
    print("Fetching agendas...")
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/agendas/", headers=headers)
    if response.status_code == 200:
        agendas = response.json()
        print(f"Found {len(agendas)} agendas")
        return agendas
    else:
        print(f"Failed to fetch agendas: {response.text}")
        return []

def get_slots(token, agenda_id, date_str):
    print(f"Fetching slots for agenda {agenda_id} on {date_str}...")
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/agendas/{agenda_id}/slots?fecha={date_str}", headers=headers)
    if response.status_code == 200:
        slots = response.json()
        print(f"Found {len(slots)} slots")
        return slots
    else:
        print(f"Failed to fetch slots: {response.text}")
        return []

def update_status(token, turno_id, status):
    print(f"Updating turno {turno_id} to {status}...")
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    response = requests.patch(f"{BASE_URL}/turnos/{turno_id}", headers=headers, json={"estado": status})
    if response.status_code == 200:
        print("Update successful")
        return response.json()
    else:
        print(f"Update failed: {response.text}")
        return None

def main():
    token = login()
    if not token:
        return

    agendas = get_agendas(token)
    if not agendas:
        return

    agenda_id = agendas[0]["id"]
    date_str = datetime.now().strftime("%Y-%m-%d")

    slots = get_slots(token, agenda_id, date_str)
    
    # Find an occupied slot
    target_slot = None
    for slot in slots:
        if slot["turno"]:
            target_slot = slot
            break
    
    if not target_slot:
        print("No occupied slots found to test update.")
        return

    turno_id = target_slot["turno"]["id"]
    print(f"Testing with Turno ID: {turno_id}, Current Status: {target_slot['turno']['estado']}")

    # Update to COMPLETADO
    updated_turno = update_status(token, turno_id, "COMPLETADO")
    if updated_turno:
        print(f"New Status: {updated_turno['estado']}")
        
        # Verify by fetching slots again
        slots_after = get_slots(token, agenda_id, date_str)
        for slot in slots_after:
            if slot["turno"] and slot["turno"]["id"] == turno_id:
                print(f"Verified Status in Slots: {slot['turno']['estado']}")
                if slot["turno"]["estado"] == "COMPLETADO":
                    print("SUCCESS: Status updated correctly.")
                else:
                    print("FAILURE: Status mismatch.")
                break

if __name__ == "__main__":
    main()
