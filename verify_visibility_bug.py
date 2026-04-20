
import sys
import os
from sqlalchemy.orm import Session
from database import SessionLocal, Base, engine
from models.user import User, UserRole
from models.agenda import Agenda
from routers.agendas import listar_agendas
import json

def test_visibility_bug():
    db = SessionLocal()
    try:
        # 1. Create a non-admin user
        user_name = "test_recepcion_bug"
        user = db.query(User).filter(User.username == user_name).first()
        if not user:
            user = User(username=user_name, password="password", role=UserRole.RECEPCION)
            db.add(user)
            db.commit()
            db.refresh(user)
        
        print(f"User Name: {user.username}, Role: {user.role}, ID: {user.id}")

        # 2. Check how many agendas are in DB
        total_agendas = db.query(Agenda).count()
        print(f"Total Agendas in DB: {total_agendas}")

        # 3. Simulate calling GET /agendas/
        context = {"username": user.username, "role": user.role}
        visible_agendas = listar_agendas(db=db, current_user=context)
        print(f"Visible Agendas for {user.username}: {len(visible_agendas)}")

        # 4. If they see everything, it's a BUG
        if len(visible_agendas) == total_agendas and total_agendas > 0:
            print("❌ CONFIRMED: Non-admin sees ALL agendas!")
        elif len(visible_agendas) == 0:
            print("✅ Non-admin sees NONE (as expected if no permissions assigned).")
        else:
            print(f"Non-admin sees {len(visible_agendas)} agendas.")

    finally:
        db.close()

if __name__ == "__main__":
    test_visibility_bug()
