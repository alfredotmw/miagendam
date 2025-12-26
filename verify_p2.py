import requests

# Config
BASE_URL = "http://localhost:8000"
USERNAME = "Alfredo"
PASSWORD = "1234"

def get_auth_headers():
    try:
        r = requests.post(f"{BASE_URL}/users/login", json={"username": USERNAME, "password": PASSWORD})
        if r.status_code == 200:
            token = r.json()["access_token"]
            return {"Authorization": f"Bearer {token}"}
        else:
            print(f"Login failed: {r.text}")
            return None
    except Exception as e:
        print(f"Login error: {e}")
        return None

def verify_p2():
    try:
        headers = get_auth_headers()
        if not headers: return

        # 1. Create Template
        print("📝 Creating Template...")
        payload = {
            "titulo": "Template Prueba P2",
            "contenido": "Paciente evoluciona favorablemente. Continue tratamiento.",
            "servicio": "TEST_P2"
        }
        res = requests.post(f"{BASE_URL}/plantillas/", json=payload, headers=headers)
        if not res.ok:
            print(f"❌ Failed to create template: {res.text}")
            return
        
        tmpl = res.json()
        tmpl_id = tmpl["id"]
        print(f"✅ Template created (ID: {tmpl_id})")

        # 2. List Templates
        print("📋 Listing Templates...")
        res = requests.get(f"{BASE_URL}/plantillas/", headers=headers)
        if not res.ok:
             print(f"❌ Failed to list: {res.text}")
             return
        
        templates = res.json()
        found = False
        for t in templates:
            if t["id"] == tmpl_id:
                found = True
                break
        
        if found:
            print("✅ Created template found in list.")
        else:
            print("❌ Template NOT found in list.")
            return

        # 3. Clean up (Delete)
        print("🗑️ Deleting Template...")
        res = requests.delete(f"{BASE_URL}/plantillas/{tmpl_id}", headers=headers)
        if not res.ok:
            print(f"❌ Failed to delete: {res.text}")
            return
        print("✅ Template deleted.")

        print("\n🎉 P2 Verification Passed!")

    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    verify_p2()
