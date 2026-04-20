
import sys
import os
import logging
from sqlalchemy.orm import Session
from database import SessionLocal, Base, engine
from models.user import User, UserRole
from models.agenda import Agenda
from routers.agendas import listar_agendas
from routers.user import UserUpdate, update_user

# Setup simple logging to console for the test
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def test_dual_permissions():
    db = SessionLocal()
    try:
        # 0. Setup: Ensure we have at least 3 agendas
        agendas = db.query(Agenda).limit(3).all()
        if len(agendas) < 3:
            print("Creating test agendas...")
            for i in range(len(agendas), 3):
                new_a = Agenda(nombre=f"Agenda Test {i+1}", tipo="CONSULTA_MEDICA")
                db.add(new_a)
            db.commit()
            agendas = db.query(Agenda).limit(3).all()
        
        a1, a2, a3 = agendas[0], agendas[1], agendas[2]
        print(f"Test Agendas: A1={a1.id}, A2={a2.id}, A3={a3.id}")

        def get_or_create_user(username, role):
            u = db.query(User).filter(User.username == username).first()
            if u:
                # Reset permissions for clean test
                u.allowed_agendas = None
                u.agendas = []
                db.commit()
            else:
                u = User(username=username, password="password", role=role)
                db.add(u)
                db.commit()
                db.refresh(u)
            return u

        # --- SCENARIO 1: Legacy CSV Only ---
        print("\n--- SCENARIO 1: Legacy CSV Only ---")
        u_legacy = get_or_create_user("u_legacy", UserRole.RECEPCION)
        u_legacy.allowed_agendas = f"{a1.id},{a2.id}"
        db.commit()
        
        visible = listar_agendas(db=db, current_user={"username": u_legacy.username, "role": "RECEPCION"})
        visible_ids = [a.id for a in visible]
        print(f"Visible IDs: {visible_ids}")
        if a1.id in visible_ids and a2.id in visible_ids and a3.id not in visible_ids:
            print("[PASS] Legacy CSV correctly filtered.")
        else:
            print("[FAIL] Legacy CSV filtering failed.")

        # --- SCENARIO 2: Many-to-Many Only ---
        print("\n--- SCENARIO 2: Many-to-Many Only ---")
        u_m2m = get_or_create_user("u_m2m", UserRole.RECEPCION)
        u_m2m.agendas = [a2, a3]
        db.commit()
        
        visible = listar_agendas(db=db, current_user={"username": u_m2m.username, "role": "RECEPCION"})
        visible_ids = [a.id for a in visible]
        print(f"Visible IDs: {visible_ids}")
        if a2.id in visible_ids and a3.id in visible_ids and a1.id not in visible_ids:
            print("[PASS] Many-to-Many correctly filtered.")
        else:
            print("[FAIL] Many-to-Many filtering failed.")

        # --- SCENARIO 3: Combined (Union) ---
        print("\n--- SCENARIO 3: Combined (Union) ---")
        u_union = get_or_create_user("u_union", UserRole.RECEPCION)
        u_union.allowed_agendas = f"{a1.id}"
        u_union.agendas = [a2]
        db.commit()
        
        visible = listar_agendas(db=db, current_user={"username": u_union.username, "role": "RECEPCION"})
        visible_ids = [a.id for a in visible]
        print(f"Visible IDs: {visible_ids}")
        if a1.id in visible_ids and a2.id in visible_ids and a3.id not in visible_ids:
            print("[PASS] Union correctly calculated.")
        else:
            print("[FAIL] Union calculation failed.")

        # --- SCENARIO 4: NO Permissions (RECEPCION) ---
        print("\n--- SCENARIO 4: NO Permissions (RECEPCION) ---")
        u_none = get_or_create_user("u_none", UserRole.RECEPCION)
        
        visible = listar_agendas(db=db, current_user={"username": u_none.username, "role": "RECEPCION"})
        print(f"Visible count: {len(visible)}")
        if len(visible) == 0:
            print("[PASS] User with no permissions sees nothing.")
        else:
            print("[FAIL] Leak detected: User with no permissions sees something.")

        # --- SCENARIO 5: Sync via update_user ---
        print("\n--- SCENARIO 5: Sync via update_user ---")
        u_sync = get_or_create_user("u_sync", UserRole.RECEPCION)
        
        # Simulate admin updating user via API
        update_data = UserUpdate(allowed_agendas=f"{a1.id},{a3.id}")
        admin_context = {"username": "admin", "role": "ADMIN"}
        
        update_user(user_id=u_sync.id, user_update=update_data, db=db, current_user=admin_context)
        
        # Verify Many-to-Many was synced
        db.refresh(u_sync)
        m2m_ids = [a.id for a in u_sync.agendas]
        print(f"Synced M2M IDs: {m2m_ids}")
        if a1.id in m2m_ids and a3.id in m2m_ids and len(m2m_ids) == 2:
            print("[PASS] Many-to-Many synced correctly during update.")
        else:
            print("[FAIL] Many-to-Many sync failed.")

        # --- SCENARIO 6: Sync via register_user ---
        print("\n--- SCENARIO 6: Sync via register_user ---")
        from routers.user import UserCreate, register_user
        
        reg_name = "u_reg_sync"
        # Clean up if exists
        old = db.query(User).filter(User.username == reg_name).first()
        if old:
            db.delete(old)
            db.commit()
            
        reg_data = UserCreate(username=reg_name, password="password", role=UserRole.RECEPCION, allowed_agendas=f"{a2.id}")
        register_user(user=reg_data, db=db, current_user=admin_context)
        
        u_reg = db.query(User).filter(User.username == reg_name).first()
        m2m_ids = [a.id for a in u_reg.agendas]
        print(f"Registered M2M IDs: {m2m_ids}")
        if a2.id in m2m_ids and len(m2m_ids) == 1:
            print("[PASS] Many-to-Many synced correctly during registration.")
        else:
            print("[FAIL] Many-to-Many sync failed during registration.")

        print("\nALL SCENARIOS VERIFIED!")

    finally:
        db.close()

if __name__ == "__main__":
    test_dual_permissions()
