from sqlalchemy.orm import Session
from database import SessionLocal
from models.user import User
from models.agenda import Agenda

def permission_fix():
    db = SessionLocal()
    try:
        users = db.query(User).all()
        agendas = db.query(Agenda).all()
        
        # Asignar todas las agendas a 'Alfredo' y 'Victoria' para testing
        all_ids = ",".join([str(a.id) for a in agendas])
        
        user_names = ["Alfredo", "Victoria"]
        
        for name in user_names:
             u = db.query(User).filter(User.username == name).first()
             if u:
                 u.allowed_agendas = all_ids
                 db.add(u)
                 print(f"✅ Granted all agendas to {name}")
        
        db.commit()

    finally:
        db.close()

if __name__ == "__main__":
    permission_fix()
