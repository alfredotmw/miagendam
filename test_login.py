import requests

def test_login():
    base_url = "http://127.0.0.1:8000"
    
    # 1. Login
    print("Testing Login...")
    try:
        resp = requests.post(f"{base_url}/users/login", json={"username": "Alfredo", "password": "1234"})
        if resp.status_code == 200:
            data = resp.json()
            token = data.get("access_token")
            print(f"✅ Login Successful. Token: {token[:20]}...")
            
            # 2. Test /me
            print("Testing /users/me...")
            headers = {"Authorization": f"Bearer {token}"}
            me_resp = requests.get(f"{base_url}/users/me", headers=headers)
            
            if me_resp.status_code == 200:
                print(f"✅ /users/me Successful: {me_resp.json()}")
            else:
                print(f"❌ /users/me Failed: {me_resp.status_code} - {me_resp.text}")
        else:
            print(f"❌ Login Failed: {resp.status_code} - {resp.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_login()
