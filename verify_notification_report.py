
import requests
import json
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8000"

def verify():
    # 1. Login
    print("🔑 Logging in...")
    resp = requests.post(f"{BASE_URL}/users/login", json={"username": "Alfredo", "password": "1234"})
    if resp.status_code != 200:
        print(f"❌ Login failed: {resp.text}")
        return
    token = resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # 2. Get Report
    today = datetime.now().strftime("%Y-%m-%d")
    print(f"📄 Fetching report for {today}...")
    resp = requests.get(f"{BASE_URL}/turnos/report?date={today}", headers=headers)
    
    if resp.status_code != 200:
        print(f"❌ Failed to get report: {resp.text}")
        return
        
    turnos = resp.json()
    print(f"✅ Report fetched. Count: {len(turnos)}")
    
    # 3. Check for the new field
    if turnos:
        first = turnos[0]
        if "recordatorio_usuario_nombre" in first:
            print("✅ 'recordatorio_usuario_nombre' field exists in response.")
            print(f"   Value: {first['recordatorio_usuario_nombre']}")
        else:
            print("❌ 'recordatorio_usuario_nombre' field MISSING in response.")
            print(f"   Keys available: {first.keys()}")
    else:
        print("⚠️ No turnos found for today, cannot verify field existence fully.")
        
    print("✅ Verification script finished.")

if __name__ == "__main__":
    verify()
