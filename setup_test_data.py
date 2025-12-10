import requests
import datetime

BASE_URL = "http://127.0.0.1:8000"

def login():
    try:
        response = requests.post(f"{BASE_URL}/users/login", json={"username": "Alfredo", "password": "123"})
        if response.status_code != 200:
             response = requests.post(f"{BASE_URL}/users/login", json={"username": "Alfredo", "password": "1234"})
        
        if response.status_code == 200:
            return response.json()["access_token"]
        else:
            print(f"Login failed: {response.text}")
            return None
    except Exception as e:
        print(f"Login error: {e}")
        return None

def create_test_turno(token):
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Get PET Agenda
    agendas = requests.get(f"{BASE_URL}/agendas/", headers=headers).json()
    pet_agenda = next((a for a in agendas if a["tipo"] == "PET"), None)
    
    if not pet_agenda:
        print("PET agenda not found")
        return

    print(f"Found PET Agenda: {pet_agenda['id']}")
    
    # Target date: Tomorrow
    target_date = (datetime.date.today() + datetime.timedelta(days=1)).isoformat()
    target_time = "09:00"
    
    # Check if slot is free (optional, but good practice)
    # For now, just try to create it. If it exists, we'll get an error or we can just use it.
    
    # Create Turno
    data = {
        "fecha": f"{target_date}T{target_time}:00",
        "hora": target_time,
        "paciente_id": 1, # Assuming patient 1 exists
        "agenda_id": pet_agenda['id'],
        "practicas_ids": [1], # Dummy practice ID
        "estado": "pendiente"
    }
    
    print(f"Creating turno for {target_date} at {target_time}...")
    response = requests.post(f"{BASE_URL}/turnos/", headers=headers, json=data)
    
    if response.status_code in [200, 201]:
        print(f"Turno created successfully! ID: {response.json()['id']}")
        return target_date, target_time
    else:
        print(f"Failed to create turno: {response.text}")
        # If it fails, maybe it already exists? Let's try to find it.
        return target_date, target_time

if __name__ == "__main__":
    token = login()
    if token:
        create_test_turno(token)
