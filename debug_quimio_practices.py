from database import SessionLocal
from models.agenda import Agenda
from models.practica import Practica
from models.agenda_practica import AgendaPractica

db = SessionLocal()

# Check Agendas
agendas = db.query(Agenda).filter(Agenda.nombre.ilike('%quimio%')).all()
print("Agendas found:", [a.nombre for a in agendas])

# Check Practice
practice = db.query(Practica).filter(Practica.nombre == "QUIMIOTERAPIA").first()
if practice:
    print(f"Practice found: {practice.nombre} (ID: {practice.id})")
else:
    print("Practice 'QUIMIOTERAPIA' NOT found.")

# Check Links
if agendas and practice:
    for agenda in agendas:
        link = db.query(AgendaPractica).filter(
            AgendaPractica.agenda_id == agenda.id,
            AgendaPractica.practica_id == practice.id
        ).first()
        if link:
            print(f"Link exists for Agenda '{agenda.nombre}' -> Practice '{practice.nombre}'")
        else:
            print(f"Link MISSING for Agenda '{agenda.nombre}' -> Practice '{practice.nombre}'")

db.close()
