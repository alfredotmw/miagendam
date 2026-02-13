import sys
import os
sys.path.append(os.getcwd())
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from database import Base, SessionLocal
from models.turno import Turno
from models.agenda import Agenda
from models.paciente import Paciente

# DB Session
db = SessionLocal()

def inspect_paciente_dni(dni):
    print(f"--- Buscando Paciente DNI: {dni} ---")
    paciente = db.query(Paciente).filter(Paciente.dni == dni).first()
    
    if not paciente:
        print("❌ Paciente no encontrado.")
        return

    print(f"Paciente: {paciente.apellido}, {paciente.nombre} (ID: {paciente.id})")
    
    turnos = db.query(Turno).filter(Turno.paciente_id == paciente.id).order_by(Turno.fecha.desc()).all()
    
    if not turnos:
        print("❌ No tiene turnos registrados.")
    
    for t in turnos:
        agenda = db.query(Agenda).filter(Agenda.id == t.agenda_id).first()
        agenda_info = f"{agenda.nombre} (ID: {agenda.id})" if agenda else "Agenda Desconocida"
        
        print(f"\n[Turno ID: {t.id}]")
        print(f"  Fecha: {t.fecha}")
        print(f"  Estado: {t.estado}")
        print(f"  Agenda: {agenda_info}")
        print(f"  Prácticas: {[p.nombre for p in t.practicas]}")

if __name__ == "__main__":
    inspect_paciente_dni("7632857")
