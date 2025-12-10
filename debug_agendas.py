import requests
import json

# Login to get token
try:
    auth_response = requests.post('http://127.0.0.1:8000/users/login', json={'username': 'Alfredo', 'password': '1234'})
    if auth_response.status_code != 200:
        print(f"Login failed: {auth_response.text}")
        exit()
    
    token = auth_response.json()['access_token']
    headers = {'Authorization': f'Bearer {token}'}
    
    # 1. Get Agendas
    print("--- Fetching Agendas ---")
    response = requests.get('http://127.0.0.1:8000/agendas/', headers=headers)
    if response.status_code == 200:
        agendas = response.json()
        print(f"Found {len(agendas)} agendas.")
        if len(agendas) > 0:
            print("Sample agenda:", json.dumps(agendas[0], indent=2, default=str))
            
            # 2. Get Slots for the first agenda (using today's date)
            first_agenda_id = agendas[0]['id']
            from datetime import date
            today = date.today().isoformat()
            print(f"\n--- Fetching Slots for Agenda {first_agenda_id} on {today} ---")
            
            slots_url = f'http://127.0.0.1:8000/agendas/{first_agenda_id}/slots?fecha={today}'
            slots_response = requests.get(slots_url, headers=headers)
            
            if slots_response.status_code == 200:
                slots = slots_response.json()
                print(f"Found {len(slots)} slots.")
                if len(slots) > 0:
                    print("Sample slot:", json.dumps(slots[0], indent=2, default=str))
            else:
                print(f"Failed to get slots: {slots_response.text}")
                
    else:
        print(f"Failed to get agendas: {response.text}")

except Exception as e:
    print(f"Error: {e}")
