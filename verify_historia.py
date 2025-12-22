from database import SessionLocal
from models.paciente import Paciente
from models.historia_clinica import HistoriaClinica
from models.turno import Turno
from models.agenda import Agenda
from datetime import datetime
from routers.historia_clinica import get_timeline

def test_historia():
    db = SessionLocal()
    try:
        # 1. Create Mock Patient
        p = db.query(Paciente).filter(Paciente.dni == "TEST_HISTORIA").first()
        if not p:
            print("Creating test patient...")
            p = Paciente(nombre="Test", apellido="Historia", dni="TEST_HISTORIA")
            db.add(p)
            db.commit()
            db.refresh(p)
        
        print(f"Patient ID: {p.id}")

        # 2. Add Mock Note
        print("Adding mock note...")
        note = HistoriaClinica(paciente_id=p.id, texto="Evolucion favorable test", servicio="TEST")
        db.add(note)
        db.commit()

        # 3. Add Mock Turno (if agenda exists)
        agenda = db.query(Agenda).first()
        if agenda:
            print("Adding mock turno...")
            t = Turno(fecha=datetime.now(), hora="10:00", paciente_id=p.id, agenda_id=agenda.id, estado="COMPLETADO")
            db.add(t)
            db.commit()

        # 4. Fetch Timeline
        print("Fetching timeline...")
        resp = get_timeline(p.id, db)
        print(f"Timeline items: {len(resp.timeline)}")
        for item in resp.timeline:
            print(f" - {item.tipo} | {item.descripcion} | {item.fecha}")

        print("Verification SUCCESS")

    except Exception as e:
        print(f"Verification FAILED: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    test_historia()
