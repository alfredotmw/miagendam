from database import SessionLocal
from models.turno import Turno
from models.paciente import Paciente
from models.agenda import Agenda
from sqlalchemy import extract

def check_patient_turnos():
    db = SessionLocal()
    try:
        # Buscar paciente por apellido
        pacientes = db.query(Paciente).filter(Paciente.apellido.ilike("%Nuñez%"), Paciente.nombre.ilike("%Mirta Elena%")).all()
        
        if not pacientes:
            print("No se encontró al paciente Nuñez Mirta Elena")
            return

        for p in pacientes:
            print(f"Paciente encontrado: {p.apellido}, {p.nombre} (ID: {p.id})")
            
            # Buscar turnos el 29/01/2026
            # Nota: SQLite almacena fechas como strings o datetime. Asumimos datetime standard.
            # Filtrar por año, mes, dia
            turnos = db.query(Turno).filter(
                Turno.paciente_id == p.id,
                extract('year', Turno.fecha) == 2026,
                extract('month', Turno.fecha) == 1,
                extract('day', Turno.fecha) == 29
            ).all()
            
            if not turnos:
                print(f"  No se encontraron turnos para el 29/01/2026")
                continue
                
            for t in turnos:
                print(f"  Turno ID: {t.id}")
                print(f"    Fecha: {t.fecha}")
                print(f"    Hora: {t.hora}")
                print(f"    Agenda: {t.agenda.nombre if t.agenda else 'N/A'}")
                print(f"    Prácticas asociadas (Relation 'practicas'):")
                if t.practicas:
                    for prac in t.practicas:
                        print(f"      - {prac.nombre} (ID: {prac.id})")
                else:
                    print("      Ninguna")
                    
                print(f"    Práctica única (Relation 'practica'): {t.practica.nombre if t.practica else 'Ninguna'}")

    finally:
        db.close()

if __name__ == "__main__":
    check_patient_turnos()
