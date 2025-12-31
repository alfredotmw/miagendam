from datetime import datetime, timedelta
from database import SessionLocal
from models.turno import Turno
from models.paciente import Paciente
from models.agenda import Agenda
from models.practica import Practica
from models.radioterapia import SeguimientoRadioterapia
from routers.turnos import crear_turno
from schemas.turno import TurnoCreate

def verify():
    db = SessionLocal()
    print("Verifying Multiple Treatments Logic...")
    
    # Setup Patient
    paciente = db.query(Paciente).filter(Paciente.dni == "88888888").first()
    if not paciente:
        paciente = Paciente(nombre="Multi", apellido="Treat", dni="88888888", fecha_nacimiento=datetime(1980,1,1))
        db.add(paciente)
        db.commit()

    # Clear previous tracking
    db.query(SeguimientoRadioterapia).filter(SeguimientoRadioterapia.paciente_id == paciente.id).delete()
    db.commit()

    agenda = db.query(Agenda).first()
    practica = db.query(Practica).first()

    from models.medico import MedicoDerivante
    medico = db.query(MedicoDerivante).first()
    if not medico:
        medico = MedicoDerivante(nombre="Derivante Test", telefono="123")
        db.add(medico)
        db.commit()

    # TEST 1: First Treatment
    print("\n--- TEST 1: First Treatment ---")
    t1 = TurnoCreate(
        fecha=datetime.now() - timedelta(days=100),
        hora="10:00", duracion=15, paciente_id=paciente.id, agenda_id=agenda.id, practicas_ids=[practica.id],
        medico_derivante_id=medico.id,
        crear_seguimiento=True, patologia="T1"
    )
    crear_turno(t1, db=db, current_user={"username": "admin"})
    
    seg1 = db.query(SeguimientoRadioterapia).filter(SeguimientoRadioterapia.paciente_id == paciente.id).order_by(SeguimientoRadioterapia.id.desc()).first()
    print(f"Seg 1 ID: {seg1.id}, Patologia: {seg1.patologia}")

    # Mark as FINISHED long ago
    seg1.fecha_fin = (datetime.now() - timedelta(days=70)).date()
    db.commit()
    print(f"Set Seg 1 Finished 70 days ago: {seg1.fecha_fin}")

    # TEST 2: New Treatment (should be NEW because > 60 days)
    print("\n--- TEST 2: New Treatment (After Gap) ---")
    t2 = TurnoCreate(
        fecha=datetime.now(),
        hora="11:00", duracion=15, paciente_id=paciente.id, agenda_id=agenda.id, practicas_ids=[practica.id],
        medico_derivante_id=medico.id,
        crear_seguimiento=True, patologia="T2"
    )
    crear_turno(t2, db=db, current_user={"username": "admin"})

    seg2 = db.query(SeguimientoRadioterapia).filter(SeguimientoRadioterapia.paciente_id == paciente.id).order_by(SeguimientoRadioterapia.id.desc()).first()
    print(f"Seg 2 ID: {seg2.id}, Patologia: {seg2.patologia}")
    
    if seg2.id != seg1.id:
        print("PASS: Created NEW record")
    else:
        print("FAIL: Reused OLD record")

    # TEST 3: Continued Treatment (should Reuse Seg 2)
    print("\n--- TEST 3: Continued Treatment ---")
    t3 = TurnoCreate(
        fecha=datetime.now() + timedelta(days=2),
        hora="12:00", duracion=15, paciente_id=paciente.id, agenda_id=agenda.id, practicas_ids=[practica.id],
        medico_derivante_id=medico.id,
        crear_seguimiento=True, patologia="T2-CONT"
    )
    crear_turno(t3, db=db, current_user={"username": "admin"})

    seg3 = db.query(SeguimientoRadioterapia).filter(SeguimientoRadioterapia.paciente_id == paciente.id).order_by(SeguimientoRadioterapia.id.desc()).first()
    print(f"Seg 3 ID: {seg3.id}")

    if seg3.id == seg2.id:
        print("PASS: Reused CURRENT record")
    else:
        print("FAIL: Created NEW record unexpectedly")

if __name__ == "__main__":
    verify()
