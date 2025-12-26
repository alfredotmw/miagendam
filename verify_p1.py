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

def verify_p1():
    try:
        headers = get_auth_headers()
        if not headers: return

        # 1. Get a patient ID (any)
        print("🔍 Searching for patient...")
        res = requests.get(f"{BASE_URL}/pacientes/?q=AGUIRRE", headers=headers)
        if not res.ok or not res.json():
             res = requests.get(f"{BASE_URL}/pacientes/", headers=headers)
             if not res.ok or not res.json():
                print("❌ No patients found.")
                return
        
        patient_id = res.json()[0]["id"]
        print(f"✅ Found patient ID: {patient_id}")

        # 2. Create Note with Oncology Fields
        print("📝 Creating Note with Oncology Fields...")
        payload = {
            "paciente_id": patient_id,
            "servicio": "ONCOLOGIA P1",
            "motivo_consulta": "Test P1 Oncology Fields",
            "ecog": 1,
            "tnm": "T2N0M1",
            "estadio": "IV",
            "toxicidad": "Nautropenia G1",
            "accion": "GUARDAR"
        }
        res = requests.post(f"{BASE_URL}/historia-clinica/", json=payload, headers=headers)
        if not res.ok:
            print(f"❌ Failed to create note: {res.text}")
            return
        
        note = res.json()
        note_id = note["id"]
        
        # Verify fields
        if note["ecog"] == 1 and note["tnm"] == "T2N0M1" and note["estadio"] == "IV":
            print(f"✅ Note created (ID: {note_id}) with Oncology Data correct.")
        else:
            print(f"❌ Data mismatch: {note}")
            return

        # 3. Update Oncology Fields
        print("✏️ Updating Oncology Fields...")
        update_payload = {
            "paciente_id": patient_id,
            "servicio": "ONCOLOGIA P1",
            "motivo_consulta": "Test P1 Updated",
            "ecog": 2, # Changed
            "tnm": "T2N1M1", # Changed
            "estadio": "IVB",
            "toxicidad": "Anemia G2",
            "accion": "GUARDAR"
        }
        res = requests.put(f"{BASE_URL}/historia-clinica/{note_id}", json=update_payload, headers=headers)
        if not res.ok:
            print(f"❌ Failed to update note: {res.text}")
            return
        
        updated = res.json()
        if updated["ecog"] == 2 and updated["tnm"] == "T2N1M1":
            print("✅ Oncology fields updated successfully.")
        else:
            print(f"❌ update mismatch: {updated}")
            return

        print("\n🎉 P1 Verification Passed!")

    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    verify_p1()
