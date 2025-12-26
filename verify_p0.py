import requests
import sys

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

def verify_p0():
    try:
        headers = get_auth_headers()
        if not headers: return

        # 1. Get a patient ID (any)
        print("🔍 Searching for patient...")
        res = requests.get(f"{BASE_URL}/pacientes/?q=AGUIRRE", headers=headers)
        if not res.ok or not res.json():
            # Try getting ALL patients if search fails
            res = requests.get(f"{BASE_URL}/pacientes/", headers=headers)
            if not res.ok or not res.json():
                print("❌ No patients found to test with.")
                return
        
        patient_id = res.json()[0]["id"]
        print(f"✅ Found patient ID: {patient_id}")

        # 2. Create Draft
        print("📝 Creating Draft Note...")
        draft_payload = {
            "paciente_id": patient_id,
            "servicio": "TEST P0",
            "motivo_consulta": "Test Draft",
            "accion": "GUARDAR"
        }
        res = requests.post(f"{BASE_URL}/historia-clinica/", json=draft_payload, headers=headers)
        if not res.ok:
            print(f"❌ Failed to create draft: {res.text}")
            return
        note = res.json()
        note_id = note["id"]
        if note.get("estado") != "BORRADOR":
            print(f"❌ Status mismatch. Expected BORRADOR, got {note.get('estado')}")
            return
        print(f"✅ Draft created (ID: {note_id}) with status BORRADOR")

        # 3. Edit Draft
        print("✏️ Editing Draft...")
        edit_payload = {
            "paciente_id": patient_id,
            "servicio": "TEST P0",
            "motivo_consulta": "Test Draft EDITED",
            "accion": "GUARDAR"
        }
        res = requests.put(f"{BASE_URL}/historia-clinica/{note_id}", json=edit_payload, headers=headers)
        if not res.ok:
            print(f"❌ Failed to edit draft: {res.text}")
            return
        updated_note = res.json()
        if updated_note["motivo_consulta"] != "Test Draft EDITED":
            print("❌ Content not updated.")
            return
        print("✅ Draft edited successfully.")

        # 4. Sign Note
        print("🔒 Signing Note...")
        sign_payload = {
            "paciente_id": patient_id,
            "servicio": "TEST P0",
            "motivo_consulta": "Test Draft EDITED",
            "accion": "FIRMAR"
        }
        res = requests.put(f"{BASE_URL}/historia-clinica/{note_id}", json=sign_payload, headers=headers)
        if not res.ok:
            print(f"❌ Failed to sign note: {res.text}")
            return
        signed_note = res.json()
        if signed_note["estado"] != "FIRMADO":
            print(f"❌ Status mismatch. Expected FIRMADO, got {signed_note['estado']}")
            return
        print("✅ Note signed. Status is FIRMADO.")

        # 5. Attempt Edit on Signed Note (Should Fail)
        print("🚫 Attempting to edit Signed Note (Should Fail)...")
        res = requests.put(f"{BASE_URL}/historia-clinica/{note_id}", json=edit_payload, headers=headers)
        if res.status_code == 403:
            print("✅ Correctly blocked with 403.")
        else:
            print(f"❌ Failed. Expected 403, got {res.status_code}")
            return

        print("\n🎉 P0 Verification Passed!")

    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    verify_p0()
