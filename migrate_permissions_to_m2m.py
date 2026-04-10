
from database import SessionLocal
from models.user import User
from models.agenda import Agenda
from sqlalchemy.orm import Session
import logging

logging.basicConfig(level=logging.INFO)

def migrate_permissions():
    db = SessionLocal()
    try:
        users = db.query(User).all()
        all_agendas = db.query(Agenda).all()
        agenda_map = {a.id: a for a in all_agendas}
        
        print(f"Iniciando migración de permisos para {len(users)} usuarios...")
        
        for u in users:
            if not u.allowed_agendas:
                print(f"User {u.username}: No legacy permissions found.")
                continue
            
            try:
                legacy_ids = [int(id_str.strip()) for id_str in u.allowed_agendas.split(',') if id_str.strip()]
                current_m2m_ids = {a.id for a in u.agendas}
                
                added_count = 0
                for aid in legacy_ids:
                    if aid in agenda_map and aid not in current_m2m_ids:
                        u.agendas.append(agenda_map[aid])
                        added_count += 1
                
                if added_count > 0:
                    print(f"User {u.username}: Added {added_count} agendas to M2M relationship.")
                else:
                    print(f"User {u.username}: All {len(legacy_ids)} legacy agendas already in M2M.")
                    
            except Exception as e:
                print(f"Error processing user {u.username}: {e}")
        
        db.commit()
        print("Migración completada exitosamente.")
        
    finally:
        db.close()

if __name__ == "__main__":
    migrate_permissions()
