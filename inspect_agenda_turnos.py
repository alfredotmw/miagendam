from database import SessionLocal
from models.turno import Turno
from models.agenda import Agenda
from sqlalchemy import extract

def check_agenda_turnos():
    db = SessionLocal()
    try:
        # ID 4 es Radioterapia Colombia segun inspect_db anterior
        agenda_id = 4 
        print(f"--- Buscando turnos Agnda {agenda_id} para 29/01/2026 ---")
        
        turnos = db.query(Turno).filter(
            Turno.agenda_id == agenda_id,
            extract('year', Turno.fecha) == 2026,
            extract('month', Turno.fecha) == 1,
            extract('day', Turno.fecha) == 29
        ).all()
        
        if not turnos:
            print("No se encontraron turnos en esa fecha/agenda.")
        
        for t in turnos:
            p = t.paciente
            print(f"\nTurno ID: {t.id} | Hora: {t.hora}")
            print(f"  Paciente: {p.apellido}, {p.nombre} (DNI: {p.dni})")
            
            # Revisar practicas (Many-to-Many)
            print(f"  t.practicas (len={len(t.practicas)}):")
            for prac in t.practicas:
                print(f"    - ID: {prac.id} | Nombre: '{prac.nombre}' | Categoria: {prac.categoria}")
                
            # Revisar practica legacy (ForeignKey simple)
            print(f"  t.practica (Legacy ID={t.practica_id}): {t.practica.nombre if t.practica else 'None'}")

    finally:
        db.close()

if __name__ == "__main__":
    check_agenda_turnos()
