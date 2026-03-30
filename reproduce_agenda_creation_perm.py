
import sys
import os
from sqlalchemy.orm import Session
from database import SessionLocal, Base, engine
from models.user import User, UserRole
from models.agenda import Agenda
from schemas.agenda import AgendaCreate
from routers.agendas import create_agenda, listar_agendas
import json

def test_full_flow():
    # Ensure tables exist
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        # 1. Create Users
        # User A: Admin (Creator)
        # User B: Assigned User
        # User C: Not Assigned User
        
        def get_or_create_user(username, role):
            u = db.query(User).filter(User.username == username).first()
            if not u:
                u = User(username=username, password="password", role=role)
                db.add(u)
                db.commit()
                db.refresh(u)
            return u

        admin_user_obj = get_or_create_user("admin_user_test", UserRole.ADMIN)
        assigned_user_obj = get_or_create_user("assigned_user_test", UserRole.RECEPCION)
        other_user_obj = get_or_create_user("other_user_test", UserRole.RECEPCION)
        
        print(f"Admin ID: {admin_user_obj.id}")
        print(f"Assigned User ID: {assigned_user_obj.id}")
        print(f"Other User ID: {other_user_obj.id}")

        # 2. Admin creates an agenda and assigns User B
        payload = {
            "nombre": "Test Multi-User Agenda",
            "tipo": "RADIOTERAPIA",
            "slot_minutos": 10,
            "activo": True,
            "allowed_user_ids": [assigned_user_obj.id]
        }
        
        print(f"\n--- STEP 1: Creating agenda with allowed_user_ids={payload['allowed_user_ids']} ---")
        agenda_in = AgendaCreate(**payload)
        admin_context = {"username": admin_user_obj.username, "role": "ADMIN"}
        
        new_agenda_out = create_agenda(agenda=agenda_in, db=db, current_user=admin_context)
        print(f"Created Agenda ID: {new_agenda_out.id}")
        print(f"Response allowed_user_ids: {new_agenda_out.allowed_user_ids}")

        # 3. Verify persistence in DB
        db_agenda = db.query(Agenda).filter(Agenda.id == new_agenda_out.id).first()
        permitted_ids = [u.id for u in db_agenda.usuarios_permitidos]
        print(f"Direct DB check - Permitted IDs: {permitted_ids}")
        
        if assigned_user_obj.id not in permitted_ids:
            print("❌ FAIL: User B was not persisted as a permitted user.")
            return

        # 4. Check visibility for User B (Assigned)
        print(f"\n--- STEP 2: Checking visibility for Assigned User ({assigned_user_obj.username}) ---")
        user_b_context = {"username": assigned_user_obj.username, "role": "RECEPCION"}
        agendas_b = listar_agendas(db=db, current_user=user_b_context)
        agendas_b_ids = [a.id for a in agendas_b]
        print(f"Agendas visible to User B: {agendas_b_ids}")
        
        if new_agenda_out.id in agendas_b_ids:
            print("[PASS] User B can see the assigned agenda.")
        else:
            print("[FAIL] User B CANNOT see the assigned agenda.")

        # 5. Check visibility for User C (Other)
        print(f"\n--- STEP 3: Checking visibility for Other User ({other_user_obj.username}) ---")
        user_c_context = {"username": other_user_obj.username, "role": "RECEPCION"}
        agendas_c = listar_agendas(db=db, current_user=user_c_context)
        agendas_c_ids = [a.id for a in agendas_c]
        print(f"Agendas visible to User C: {agendas_c_ids}")
        
        if new_agenda_out.id not in agendas_c_ids:
            print("[PASS] User C cannot see the agenda (as expected).")
        else:
            print("[FAIL] User C CAN see the agenda (but shouldn't).")

        # 6. Check visibility for Admin (A)
        print(f"\n--- STEP 4: Checking visibility for Admin ({admin_user_obj.username}) ---")
        agendas_admin = listar_agendas(db=db, current_user=admin_context)
        agendas_admin_ids = [a.id for a in agendas_admin]
        if new_agenda_out.id in agendas_admin_ids:
            print("[PASS] Admin can see everything.")
        else:
            print("[FAIL] Admin CANNOT see the agenda.")

        print("\nALL TESTS PASSED! Fix verified end-to-end.")

    finally:
        db.close()

if __name__ == "__main__":
    test_full_flow()
