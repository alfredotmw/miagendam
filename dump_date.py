from database import SessionLocal
from models.turno import Turno
from models.paciente import Paciente
from models.agenda import Agenda
from sqlalchemy import extract

def dump_date():
    db = SessionLocal()
    try:
        fechas = [
            (2026, 1, 29),
            (2025, 1, 29)
        ]
        
        for y, m, d in fechas:
            print(f"--- Buscando turnos para {y}-{m}-{d} ---")
            turnos = db.query(Turno).filter(
                extract('year', Turno.fecha) == y,
                extract('month', Turno.fecha) == m,
                extract('day', Turno.fecha) == d
            ).all()
            
            if not turnos:
                print("  No hay turnos.")
            
            for t in turnos:
                p_nombre = f"{t.paciente.apellido}, {t.paciente.nombre}" if t.paciente else "N/A"
                print(f"  [{t.hora}] {p_nombre} - Agenda: {t.agenda.nombre if t.agenda else 'N/A'}")
                if "Nu" in p_nombre or "nez" in p_nombre:
                     print(f"     *** POSIBLE COINCIDENCIA ***")
                     print(f"     Practicas: {[p.nombre for p in t.practicas]}")
                     print(f"     Practica (legacy): {t.practica.nombre if t.practica else 'None'}")
                     
    finally:
        db.close()

if __name__ == "__main__":
    dump_date()
