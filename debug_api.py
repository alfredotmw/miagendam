import requests
import json

# Login to get token
try:
    # Correct endpoint and JSON body, and correct password
    auth_response = requests.post('http://127.0.0.1:8000/users/login', json={'username': 'Alfredo', 'password': '1234'})
    if auth_response.status_code != 200:
        print(f"Login failed: {auth_response.text}")
        exit()
    
    token = auth_response.json()['access_token']
    headers = {'Authorization': f'Bearer {token}'}
    
    # Get turnos
    response = requests.get('http://127.0.0.1:8000/turnos/', headers=headers)
    if response.status_code == 200:
        turnos = response.json()
        print(f"Found {len(turnos)} turnos.")
        if len(turnos) > 0:
            print("Sample turno:", json.dumps(turnos[0], indent=2, default=str))
    else:
        print(f"Failed to get turnos: {response.text}")

except Exception as e:
    print(f"Error: {e}")
