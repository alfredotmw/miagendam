from sqlalchemy.orm import Session
from database import SessionLocal
# Importar todos los modelos para asegurar que SQLAlchemy los registre
from models.paciente import Paciente
from models.turno import Turno
from models.agenda import Agenda
from models.practica import Practica
from models.medico import MedicoDerivante
from models.turno_practica import TurnoPractica
import random

def fix_data():
    db = SessionLocal()
    print("🔧 Reparando y Actualizando Datos...")

    # 1. Asignar Sexo a Pacientes que no lo tienen
    pacientes = db.query(Paciente).filter(Paciente.sexo == None).all()
    print(f"   Pacientes sin sexo: {len(pacientes)}")
    
    for p in pacientes:
        # Asignación simple basada en nombre (muy básica, solo para demo)
        if p.nombre.endswith("a"):
            p.sexo = "F"
        else:
            p.sexo = "M"
    
    db.commit()
    print("   ✅ Sexo asignado a pacientes existentes.")

    # 2. Actualizar Estados de Turnos para Demo
    # Vamos a poner algunos turnos como 'completado' y otros 'ausente'
    turnos = db.query(Turno).all()
    
    if len(turnos) >= 1:
        turnos[0].estado = "completado"
        print(f"   ✅ Turno ID {turnos[0].id} marcado como 'completado'.")
    
    if len(turnos) >= 2:
        turnos[1].estado = "ausente"
        print(f"   ✅ Turno ID {turnos[1].id} marcado como 'ausente'.")

    db.commit()
    db.close()
    print("✅ Datos actualizados correctamente.")

if __name__ == "__main__":
    fix_data()
