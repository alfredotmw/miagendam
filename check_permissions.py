from database import SessionLocal
from models.user import User
from models.agenda import Agenda
from sqlalchemy.orm import Session

def check_permissions():
    db = SessionLocal()
    try:
        users = db.query(User).all()
        print(f"📊 Total de usuarios: {len(users)}")
        
        for u in users:
            print(f"\n👤 Usuario: {u.username} (Rol: {u.role})")
            
            # Agendas permitidas vía Many-to-Many
            agendas_m2m = u.agendas
            print(f"   - Agendas permitidas (M2M): {[a.nombre for a in agendas_m2m]}")
            
            # Si es MEDICO, agendas permitidas vía nombre profesional
            if u.role == "MEDICO":
                search_term = f"%{u.username}%"
                agendas_med = db.query(Agenda).filter(Agenda.profesional.ilike(search_term)).all()
                print(f"   - Agendas permitidas (Profesional): {[a.nombre for a in agendas_med]}")

        agendas = db.query(Agenda).all()
        print(f"\n📅 Total de agendas registradas: {len(agendas)}")
        for a in agendas:
            users_p = a.usuarios_permitidos
            print(f"   - {a.nombre} (ID: {a.id}) | Usuarios permitidos: {[u.username for u in users_p]}")

    finally:
        db.close()

if __name__ == "__main__":
    check_permissions()
