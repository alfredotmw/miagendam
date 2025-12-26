
import requests
import json
import sys

BASE_URL = "http://localhost:8000"
ADMIN_USER = "Alfredo" # Updated based on reset_admin.py
ADMIN_PASS = "1234" # Updated based on reset_admin.py

def login(username, password):
    url = f"{BASE_URL}/users/login"
    payload = {"username": username, "password": password}
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        return response.json().get("access_token")
    except Exception as e:
        print(f"Login failed for {username}: {e}")
        return None

def create_user(admin_token, new_username, new_password, role, allowed_agendas):
    url = f"{BASE_URL}/users/register"
    headers = {"Authorization": f"Bearer {admin_token}"}
    payload = {
        "username": new_username,
        "password": new_password,
        "role": role,
        "allowed_agendas": allowed_agendas
    }
    try:
        response = requests.post(url, json=payload, headers=headers)
        if response.status_code == 400 and "ya existe" in response.text:
            print(f"User {new_username} already exists.")
            return True
        response.raise_for_status()
        print(f"User {new_username} created. Response: {response.json()}")
        return True
    except Exception as e:
        print(f"Create user failed: {e}")
        return False

def check_agendas(user_token):
    url = f"{BASE_URL}/agendas/"
    headers = {"Authorization": f"Bearer {user_token}"}
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        agendas = response.json()
        print(f"Agendas visible: {[a['id'] for a in agendas]}")
        return agendas
    except Exception as e:
        print(f"Get agendas failed: {e}")
        return []

def main():
    print("--- 1. Login as Admin ---")
    admin_token = login(ADMIN_USER, ADMIN_PASS)
    if not admin_token:
        print("Cannot proceed without admin token.")
        return

    print("\n--- 2. Create User with Restricted Permissions ---")
    test_user = "test_medico_custom"
    test_pass = "123456"
    test_agendas = "1" # Only agenda 1
    
    if create_user(admin_token, test_user, test_pass, "MEDICO", test_agendas):
        print("\n--- 3. Login as Restricted User ---")
        user_token = login(test_user, test_pass)
        
        if user_token:
            print("\n--- 4. Verify Visible Agendas ---")
            agendas = check_agendas(user_token)
            
            visible_ids = [a['id'] for a in agendas]
            if visible_ids == [1]:
                print("SUCCESS: User can only see agenda 1.")
            else:
                print(f"FAILURE: User sees {visible_ids}, expected [1].")

if __name__ == "__main__":
    main()
