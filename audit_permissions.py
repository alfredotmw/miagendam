from database import SessionLocal
from models.user import User, UserRole
from models.agenda import Agenda
from sqlalchemy.orm import Session

def audit():
    db = SessionLocal()
    try:
        users = db.query(User).all()
        all_agendas = db.query(Agenda).all()
        agenda_map = {a.id: a.nombre for a in all_agendas}
        
        print(f"{'USUARIO':<20} | {'ROL':<12} | {'AGENDAS ACTUALES':<10} | {'ESTADO/PROPUESTA'}")
        print("-" * 80)
        
        for u in users:
            current_agendas = [a.nombre for a in u.agendas]
            count = len(current_agendas)
            
            status = "OK"
            propuesta = ""
            
            if count == len(all_agendas):
                status = "⚠️ SOBRE-ASIGNADO (Acceso Total)"
            elif count == 0 and u.role != UserRole.ADMIN:
                status = "🚫 BLOQUEADO (0 agendas)"
            
            # Evaluación para Médicos
            if u.role == UserRole.MEDICO:
                matched = [a.nombre for a in all_agendas if a.profesional and u.username.lower() in a.profesional.lower()]
                if matched:
                    if not any(m in current_agendas for m in matched):
                        propuesta = f"Sugerido: Vincular a {matched}"
                else:
                    propuesta = "No se encontró coincidencia por nombre"

            print(f"{u.username:<20} | {u.role:<12} | {count:<16} | {status}")
            if propuesta:
                print(f"{' ':<35} 💡 {propuesta}")

    finally:
        db.close()

if __name__ == "__main__":
    audit()
