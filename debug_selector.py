from sqlalchemy.orm import Session
from database import SessionLocal
from models.user import User, UserRole
from models.agenda import Agenda

def check_data():
    db = SessionLocal()
    try:
        medicos = db.query(User).all()
        agendas = db.query(Agenda).all()

        print(f"--- Medicos ({len(medicos)}) ---")
        for m in medicos:
            print(f"User: '{m.username}'")

        print(f"\n--- Agendas ({len(agendas)}) ---")
        for a in agendas:
            print(f"Agenda: '{a.nombre}' - Tipo: '{a.tipo}' - Profesional: '{a.profesional}'")

        print("\n--- Matching Check ---")
        for m in medicos:
            matches = [a for a in agendas if a.profesional == m.username]
            print(f"Medico '{m.username}' sees {len(matches)} agendas: {[a.nombre for a in matches]}")
            
    finally:
        db.close()

if __name__ == "__main__":
    check_data()
