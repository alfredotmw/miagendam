from datetime import datetime, timedelta
from database import SessionLocal
from models.turno import Turno
from models.paciente import Paciente
from models.agenda import Agenda
from models.practica import Practica
from routers.turnos import crear_turno
from schemas.turno import TurnoCreate
from fastapi import HTTPException

def reproduce_overlap():
    db = SessionLocal()
    print("Reproduction: Patient double booking in different services...")
    
    # Setup
    # Let's pick ID 1 (QUIMIOTERAPIA SAN MARTIN) and ID 3 (RADIOTERAPIA SAN MARTIN)
    agenda_quimio = db.get(Agenda, 1)
    agenda_radio = db.get(Agenda, 3)
    
    # Get a practice for each
    practica_quimio = db.query(Practica).filter(Practica.nombre.like("%QUIMIO%")).first()
    if not practica_quimio: practica_quimio = db.query(Practica).first()
    
    practica_radio = db.query(Practica).filter(Practica.nombre.like("%RADIO%")).first()
    if not practica_radio: practica_radio = db.query(Practica).first()
    
    pac_id = 1 # Assuming patient 1 exists
    paciente = db.get(Paciente, pac_id)
    if not paciente:
        paciente = db.query(Paciente).first()
        pac_id = paciente.id

    print(f"Using Paciente: {paciente.nombre} (ID: {pac_id})")
    print(f"Agenda 1: {agenda_quimio.nombre} (Tipo: {agenda_quimio.tipo})")
    print(f"Agenda 2: {agenda_radio.nombre} (Tipo: {agenda_radio.tipo})")

    fecha_test = datetime.now().replace(hour=12, minute=0, second=0, microsecond=0) + timedelta(days=5)
    if fecha_test.weekday() == 6: # Sunday
        fecha_test += timedelta(days=1)
    
    # 1. Create turn in Quimio at 12:00
    print(f"\n1. Creating turn in {agenda_quimio.nombre} at 12:00...")
    turno_quimio_in = TurnoCreate(
        fecha=fecha_test,
        hora="12:00",
        duracion_custom=60,
        paciente_id=pac_id,
        agenda_id=agenda_quimio.id,
        practicas_ids=[practica_quimio.id],
        medico_derivante_nombre="DR. TEST",
        crear_seguimiento=False
    )
    
    try:
        crear_turno(turno_quimio_in, db=db, current_user={"username": "admin"})
        print("Success creating first turn.")
    except HTTPException as e:
        print(f"Error creating first turn: {e.detail}")
        return

    # 2. Try to create turn in Radio at 12:00 for the SAME patient
    print(f"\n2. Trying to create turn in {agenda_radio.nombre} at 12:00 for SAME patient...")
    turno_radio_in = TurnoCreate(
        fecha=fecha_test,
        hora="12:00",
        duracion_custom=10,
        paciente_id=pac_id,
        agenda_id=agenda_radio.id,
        practicas_ids=[practica_radio.id],
        medico_derivante_nombre="DR. TEST",
        crear_seguimiento=False
    )
    
    try:
        crear_turno(turno_radio_in, db=db, current_user={"username": "admin"})
        print("Success creating second turn! (Issue NOT reproduced locally if this prints)")
    except HTTPException as e:
        print(f"CAUGHT EXPECTED ERROR: {e.detail}")
    except Exception as e:
        print(f"Caught unexpected error: {e}")

    # Cleanup (Rollback or delete)
    db.rollback() 
    db.close()

if __name__ == "__main__":
    reproduce_overlap()
