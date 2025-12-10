import requests
import json
from datetime import date, timedelta

# Login to get token
try:
    auth_response = requests.post('http://127.0.0.1:8000/users/login', json={'username': 'Alfredo', 'password': '1234'})
    if auth_response.status_code != 200:
        print(f"Login failed: {auth_response.text}")
        exit()
    
    token = auth_response.json()['access_token']
    headers = {'Authorization': f'Bearer {token}'}
    
    # Get turnos for tomorrow
    tomorrow = (date.today() + timedelta(days=1)).isoformat()
    print(f"--- Checking Turnos for {tomorrow} ---")
    
    # We can filter client side if endpoint doesn't support date filtering directly or fetch all
    response = requests.get('http://127.0.0.1:8000/turnos/?limit=100', headers=headers)
    if response.status_code == 200:
        turnos = response.json()
        found = False
        for t in turnos:
            if t['fecha'].startswith(tomorrow):
                print("Found turn for tomorrow:")
                print(json.dumps(t, indent=2, default=str))
                found = True
        
        if not found:
            print("No turnos found for tomorrow.")
    else:
        print(f"Failed to get turnos: {response.text}")

except Exception as e:
    print(f"Error: {e}")
