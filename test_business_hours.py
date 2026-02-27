import requests
import json

# Configuration
BASE_URL = "http://localhost:10000" # Assuming server is or will be running here
# Actually, since I'm running in the same environment, I can test against the DB or start the server.
# But usually I should try to use the API for full verification.
# For now, I'll use a local script that calls the router functions directly via TestClient if possible, 
# or just a script that simulates the POST.

# Let's use FastAPI TestClient
from fastapi.testclient import TestClient
from main import app
from database import SessionLocal
from sqlalchemy import text

client = TestClient(app)

def get_auth_token():
    # We'll try to find a valid user or create one for testing
    # For simplicity, let's assume 'admin' exists. 
    # Or we can override the dependency.
    pass

# We'll use dependency override to bypass AUTH for testing
from auth.jwt import get_current_user
app.dependency_overrides[get_current_user] = lambda: {"username": "testuser", "role": "ADMIN"}

def test_business_hours():
    print("--- TESTING BUSINESS HOURS VALIDATION ---")
    
    # 1. Try 00:00:00
    payload = {
        "fecha": "2026-03-02T00:00:00", # Monday
        "hora": "00:00:00",
        "paciente_id": 1,
        "agenda_id": 1,
        "practicas_ids": [54], # Quimioterapia
        "medico_derivante_id": 2
    }
    
    response = client.post("/turnos/", json=payload)
    print(f"Result for 00:00:00: {response.status_code} - {response.json()}")
    assert response.status_code == 400
    assert "Horario no habilitado" in response.json()["detail"]

    # 2. Try 23:00
    payload["hora"] = "23:00"
    response = client.post("/turnos/", json=payload)
    print(f"Result for 23:00: {response.status_code} - {response.json()}")
    assert response.status_code == 400
    
    # 3. Try 06:00
    payload["hora"] = "06:00"
    response = client.post("/turnos/", json=payload)
    print(f"Result for 06:00: {response.status_code} - {response.json()}")
    assert response.status_code == 400

    print("✅ Business hours test passed.\n")

if __name__ == "__main__":
    test_business_hours()
