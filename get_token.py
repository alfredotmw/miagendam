import requests
import sys

BASE_URL = "http://127.0.0.1:8000"
USERNAME = "Alfredo"
PASSWORD = "1234"

print("Starting get_token.py...", flush=True)

try:
    r = requests.post(f"{BASE_URL}/users/login", json={"username": USERNAME, "password": PASSWORD})
    print(f"Status Code: {r.status_code}", flush=True)
    if r.status_code == 200:
        token = r.json()["access_token"]
        print(f"TOKEN_START:{token}:TOKEN_END", flush=True)
        with open("token_final.txt", "w") as f:
            f.write(token)
        print("Token written to token_final.txt", flush=True)
    else:
        print(f"Login failed: {r.text}", flush=True)
except Exception as e:
    print(f"Exception: {e}", flush=True)
