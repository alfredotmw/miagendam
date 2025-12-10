import requests
import json

BASE_URL = "http://127.0.0.1:8000"
USERNAME = "Alfredo"
PASSWORD = "123"  # Assuming this from previous context, or I'll try "1234" if this fails. 
# Wait, init_data.py said "1234".

def login():
    try:
        response = requests.post(f"{BASE_URL}/users/login", json={"username": "Alfredo", "password": "123"})
        if response.status_code != 200:
             # Try 1234
             response = requests.post(f"{BASE_URL}/users/login", json={"username": "Alfredo", "password": "1234"})
        
        if response.status_code == 200:
            return response.json()["access_token"]
        else:
            print(f"Login failed: {response.text}")
            return None
    except Exception as e:
        print(f"Login error: {e}")
        return None

def test_patch(turno_id, token):
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    data = {"estado": "COMPLETADO"}
    
    print(f"Sending PATCH to /turnos/{turno_id} with data: {data}")
    try:
        response = requests.patch(f"{BASE_URL}/turnos/{turno_id}", headers=headers, json=data)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"Request failed: {e}")

if __name__ == "__main__":
    token = login()
    if token:
        print("Login successful. Testing PATCH...")
        # Using ID 53 as seen in user logs
        test_patch(53, token)
    else:
        print("Could not get token.")
