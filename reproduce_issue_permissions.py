
import sys
from sqlalchemy.orm import Session
from database import SessionLocal
from models.user import User, UserRole
from models.agenda import Agenda
from schemas.agenda import AgendaCreate
from routers.agendas import create_agenda
import json

def test_repro():
    db = SessionLocal()
    try:
        # 1. Create a test user
        test_username = "test_user_repro"
        user = db.query(User).filter(User.username == test_username).first()
        if not user:
            user = User(username=test_username, password="password", role=UserRole.RECEPCION)
            db.add(user)
            db.commit()
            db.refresh(user)
        
        print(f"Test User ID: {user.id}")

        # 2. Simulate Agenda Creation with allowed_user_ids
        # This is what the frontend sends
        payload = {
            "nombre": "Test Agenda Repro",
            "tipo": "CONSULTA_MEDICA",
            "slot_minutos": 20,
            "activo": True,
            "allowed_user_ids": [user.id]
        }
        
        print(f"Payload sent from frontend: {json.dumps(payload)}")

        # 3. Backend receives it as AgendaCreate
        # In FastAPI, Pydantic would parse this. Let's see if AgendaCreate accepts it.
        try:
            agenda_in = AgendaCreate(**payload)
            print("AgendaCreate accepted allowed_user_ids (Wait, it shouldn't if extra='forbid' is not set, but it won't have the attribute)")
        except Exception as e:
            print(f"AgendaCreate rejected payload: {e}")
            return

        # 4. Mock the current_user (Admin)
        admin_user = {"username": "admin", "role": "ADMIN"}

        # 5. Call the router function
        new_agenda_out = create_agenda(agenda=agenda_in, db=db, current_user=admin_user)
        
        print(f"Created Agenda ID: {new_agenda_out.id}")
        print(f"Allowed User IDs in response: {new_agenda_out.allowed_user_ids}")

        # 6. Verify in DB
        db_agenda = db.query(Agenda).filter(Agenda.id == new_agenda_out.id).first()
        permitted_ids = [u.id for u in db_agenda.usuarios_permitidos]
        print(f"Actual Permitted IDs in DB: {permitted_ids}")

        if user.id not in permitted_ids:
            print("\n❌ REPRODUCTION SUCCESSFUL: User ID not found in agenda permissions!")
        else:
            print("\n✅ REPRODUCTION FAILED: User ID found in agenda permissions.")

    finally:
        # Cleanup (optional, but keep it for now)
        # db.delete(db_agenda)
        # db.commit()
        db.close()

if __name__ == "__main__":
    test_repro()
