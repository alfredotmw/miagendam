import json
from fastapi.testclient import TestClient
from main import app
from database import SessionLocal
from sqlalchemy import text
from datetime import datetime, timedelta

client = TestClient(app)

# Bypass AUTH
from auth.jwt import get_current_user
app.dependency_overrides[get_current_user] = lambda: {"username": "testuser", "role": "ADMIN"}

def test_quimio_duplicate():
    print("--- TESTING QUIMIOTERAPIA DUPLICATE PREVENTION ---")
    
    # 1. Create a turno
    payload = {
        "fecha": "2026-03-05T10:00:00", # Fixed date for testing
        "hora": "10:00",
        "paciente_id": 1,
        "agenda_id": 1,
        "practicas_ids": [54], # Quimioterapia
        "medico_derivante_id": 2
    }
    
    # Clear existing if any for this test
    with SessionLocal() as db:
        db.execute(text("DELETE FROM turnos_practicas WHERE turno_id IN (SELECT id FROM turnos WHERE paciente_id=1 AND agenda_id=1 AND DATE(fecha)='2026-03-05')"))
        db.execute(text("DELETE FROM turnos WHERE paciente_id=1 AND agenda_id=1 AND DATE(fecha)='2026-03-05'"))
        db.commit()

    print("Success: Creating first turno...")
    res1 = client.post("/turnos/", json=payload)
    print(f"First turno: {res1.status_code}")
    assert res1.status_code == 200

    # 2. Try creating the EXACT SAME turno again
    print("Failure: Creating duplicate turno (same practice, same day)...")
    res2 = client.post("/turnos/", json=payload)
    print(f"Second turno: {res2.status_code} - {res2.json()}")
    assert res2.status_code == 409
    assert "Turno duplicado" in res2.json()["detail"]

    # 3. Try different time same day (Should STILL fail because same patient+agenda+practice+day)
    print("Failure: Creating same practice, different time, same day...")
    payload["hora"] = "11:00"
    res3 = client.post("/turnos/", json=payload)
    print(f"Third turno: {res3.status_code} - {res3.json()}")
    assert res3.status_code == 409

    # 4. Try different practice same day (Should succeed)
    print("Success: Creating different practice same day...")
    payload["practicas_ids"] = [55] # Another quimio practice or different
    res4 = client.post("/turnos/", json=payload)
    print(f"Fourth turno: {res4.status_code}")
    assert res4.status_code == 200

    print("✅ Quimioterapia duplicate prevention test passed.\n")

if __name__ == "__main__":
    test_quimio_duplicate()
