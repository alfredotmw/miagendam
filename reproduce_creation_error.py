from datetime import datetime, timedelta
from database import SessionLocal
from models.turno import Turno
from models.paciente import Paciente
from models.agenda import Agenda
from models.practica import Practica
from routers.turnos import crear_turno
from schemas.turno import TurnoCreate

def reproduce():
    db = SessionLocal()
    print("Reproducing Creation Error...")
    
    # Setup
    agenda = db.query(Agenda).first()
    practica = db.query(Practica).first()
    paciente = db.query(Paciente).first()
    
    if not all([agenda, practica, paciente]):
        print("Missing base data")
        return

    turno_in = TurnoCreate(
        fecha=datetime.now() + timedelta(days=100), # Far future to avoid conflicts
        hora="10:00",
        duracion=15,
        paciente_id=paciente.id,
        agenda_id=agenda.id,
        practicas_ids=[practica.id],
        medico_derivante_nombre="Dr. Test",
        crear_seguimiento=True,
        patologia="TEST ERR"
    )
    
    try:
        print(f"Creating turno for Agenda {agenda.nombre}...")
        crear_turno(turno_in, db=db, current_user={"username": "admin"})
        print("Success!")
    except Exception as e:
        print(f"Start Error Traceback:")
        import traceback
        traceback.print_exc()
        print(f"End Error: {e}")

if __name__ == "__main__":
    reproduce()
