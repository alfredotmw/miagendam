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
    
    # Get all patients
    print("--- Checking Patients ---")
    response = requests.get('http://127.0.0.1:8000/pacientes/?limit=100', headers=headers) # Assuming endpoint exists
    if response.status_code == 200:
        pacientes = response.json()
        print(f"Found {len(pacientes)} patients.")
        for p in pacientes:
            if p['nombre'] == 'undefined' or p['apellido'] == 'undefined' or p['nombre'] is None:
                print(f"WARNING: Patient with undefined/null name: {json.dumps(p, indent=2)}")
    else:
        # Try getting turnos and checking nested patients
        print("--- Checking Turnos for Patient Data ---")
        response = requests.get('http://127.0.0.1:8000/turnos/?limit=100', headers=headers)
        if response.status_code == 200:
            turnos = response.json()
            for t in turnos:
                p = t.get('paciente')
                if p:
                    if p.get('nombre') == 'undefined' or p.get('apellido') == 'undefined':
                         print(f"WARNING: Turno {t['id']} has patient with undefined name: {json.dumps(p, indent=2)}")
                else:
                    print(f"Turno {t['id']} has no patient object.")

except Exception as e:
    print(f"Error: {e}")
