
import requests

url = "https://agendas-medicas.onrender.com/radioterapia/feed"
try:
    print(f"Checking URL: {url}")
    resp = requests.get(url, timeout=10)
    print(f"Status Code: {resp.status_code}")
    if resp.status_code == 404:
        print("CONFIRMED: Endpoint not found on server (404).")
    elif resp.status_code == 401:
        print("Endpoint exists (401 Unauthorized as expected without token).")
    else:
        print(f"Unexpected status: {resp.status_code}")
except Exception as e:
    print(f"Error checking URL: {e}")
