from database import SessionLocal
from models.radioterapia import SeguimientoRadioterapia
from models.turno import Turno
from models.agenda import Agenda
from models.practica import Practica
from sqlalchemy.orm import Session
import traceback

def check_and_autofill_debug(reg: SeguimientoRadioterapia, db: Session):
    print(f"Checking reg {reg.id}...")
    changes = False

    # 1. FECHA TAC
    if not reg.fecha_tac:
        last_tac = db.query(Turno).join(Agenda).join(Practica, Turno.practica_id == Practica.id, isouter=True).filter(
            Turno.paciente_id == reg.paciente_id,
            Turno.estado == "COMPLETADO", 
            (Agenda.tipo == "TOMOGRAFIA") | (Practica.categoria == "TOMOGRAFIA")
        ).order_by(Turno.fecha.desc()).first()
        
        if last_tac:
            reg.fecha_tac = last_tac.fecha.date()
            changes = True

    # 2. FECHA INICIO TTO
    if not reg.fecha_inicio:
        first_radio = db.query(Turno).join(Agenda).filter(
            Turno.paciente_id == reg.paciente_id,
            Agenda.tipo == "RADIOTERAPIA"
        ).order_by(Turno.fecha.asc()).first()
        
        if first_radio:
            reg.fecha_inicio = first_radio.fecha.date()
            changes = True

    # 3. FECHA FIN TTO
    last_radio = db.query(Turno).join(Agenda).filter(
        Turno.paciente_id == reg.paciente_id,
        Agenda.tipo == "RADIOTERAPIA"
    ).order_by(Turno.fecha.desc()).first()

    if last_radio:
        last_date = last_radio.fecha.date()
        # Potential crash point: if reg.fecha_fin is None? No, comparison works.
        if not reg.fecha_fin or reg.fecha_fin != last_date:
            reg.fecha_fin = last_date
            changes = True

    if changes:
        print(f"Changes detected for {reg.id}") 

def run_debug():
    db = SessionLocal()
    try:
        registros = db.query(SeguimientoRadioterapia).all()
        print(f"Found {len(registros)} registros.")
        for reg in registros:
            check_and_autofill_debug(reg, db)
        print("Autofill check PASSED.")
    except Exception as e:
        print("CRASH inside autofill:")
        traceback.print_exc()

if __name__ == "__main__":
    run_debug()
