from database import SessionLocal
from models.agenda import Agenda
from models.turno import Turno
from models.paciente import Paciente
from datetime import datetime

def debug_pet():
    db = SessionLocal()
    try:
        # 1. Find PET agendas
        pet_agendas = db.query(Agenda).filter(Agenda.nombre.ilike("%PET%")).all()
        if not pet_agendas:
            print("No se encontraron agendas con 'PET' en el nombre.")
            return

        print(f"Agendas PET encontradas: {[a.nombre for a in pet_agendas]}")
        
        estados = {}
        total_turnos = 0

        for agenda in pet_agendas:
            print(f"\n--- Agenda: {agenda.nombre} (ID: {agenda.id}) ---")
            turnos = db.query(Turno).filter(
                Turno.agenda_id == agenda.id
            ).all()

            print(f"Total turnos found in DB for this agenda: {len(turnos)}")
            for t in turnos:
                paciente_nombre = f"{t.paciente.nombre} {t.paciente.apellido}" if t.paciente else "Sin Paciente"
                print(f"Turno ID: {t.id} | Fecha: {t.fecha} | Hora: {t.hora} | Estado: {t.estado} | Paciente: {paciente_nombre}")
                
                estados[t.estado] = estados.get(t.estado, 0) + 1
                total_turnos += 1

        print("\n--- Resumen ---")
        print(f"Total turnos: {total_turnos}")
        print(f"Estados: {estados}")

    finally:
        db.close()

if __name__ == "__main__":
    debug_pet()
