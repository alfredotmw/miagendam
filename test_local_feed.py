import requests
from auth.jwt import create_access_token

def test_local():
    token = create_access_token({"sub": "admin", "role": "ADMIN"})
    url = f"http://127.0.0.1:8000/radioterapia/feed?token={token}"
    print(f"Testing {url}")
    try:
        r = requests.get(url)
        print(f"Status: {r.status_code}")
        if r.status_code == 200:
            print("Response JSON keys:", r.json()[0].keys() if r.json() else "Empty list")
        else:
            print("Error:", r.text)
    except Exception as e:
        print(f"Failed: {e}")

if __name__ == "__main__":
    test_local()
