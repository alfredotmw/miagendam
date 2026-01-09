from database import SessionLocal
from models.agenda import Agenda
from models.practica import Practica, CategoriaPractica
from models.agenda_practica import AgendaPractica

db = SessionLocal()

def fix_quimio():
    print("Beginning Quimio Fix...")
    
    # 1. Ensure Practice Exists
    practice_name = "QUIMIOTERAPIA"
    practice = db.query(Practica).filter(Practica.nombre == practice_name).first()
    
    if not practice:
        print(f"Creating practice: {practice_name}")
        practice = Practica(nombre=practice_name, categoria=CategoriaPractica.QUIMIOTERAPIA)
        db.add(practice)
        db.commit()
        db.refresh(practice)
        print(f"Created practice with ID: {practice.id}")
    else:
        print(f"Practice already exists: {practice_name} (ID: {practice.id})")

    # 2. Link to Agendas
    agendas = db.query(Agenda).filter(Agenda.nombre.ilike('%quimio%')).all()
    print(f"Found {len(agendas)} Quimio agendas.")

    for agenda in agendas:
        link = db.query(AgendaPractica).filter(
            AgendaPractica.agenda_id == agenda.id,
            AgendaPractica.practica_id == practice.id
        ).first()

        if not link:
            print(f"Linking Agenda '{agenda.nombre}' to Practice '{practice.nombre}'")
            new_link = AgendaPractica(agenda_id=agenda.id, practica_id=practice.id)
            db.add(new_link)
        else:
            print(f"Already linked: Agenda '{agenda.nombre}' -> Practice '{practice.nombre}'")

    db.commit()
    print("Fix completed successfully.")

if __name__ == "__main__":
    try:
        fix_quimio()
    except Exception as e:
        print(f"Error during fix: {e}")
    finally:
        db.close()
