from datetime import datetime, date, timedelta
from sqlalchemy.orm import Session
from database import SessionLocal
from models.paciente import Paciente
from models.medico import MedicoDerivante
from models.turno import Turno
from models.agenda import Agenda
from models.practica import Practica

def test_enhancements():
    db = SessionLocal()
    print("🧪 Probando Mejoras de Datos (Pacientes y Médicos)...\n")

    # 1. Crear Paciente con nuevos datos
    print("1️⃣  Creando Paciente con Sexo, Celular y Fecha Nacimiento...")
    fecha_nac = date(1985, 5, 20) # 40 años en 2025 aprox
    paciente = Paciente(
        nombre="Maria", 
        apellido="Gonzalez", 
        dni="99887766", 
        fecha_nacimiento=fecha_nac,
        sexo="F",
        celular="3794123456",
        email="maria@test.com"
    )
    db.add(paciente)
    db.commit()
    db.refresh(paciente)
    
    print(f"    ✅ Paciente creado: {paciente.nombre} {paciente.apellido}")
    print(f"       Sexo: {paciente.sexo}")
    print(f"       Celular: {paciente.celular}")
    print(f"       Fecha Nac: {paciente.fecha_nacimiento}")

    # Calcular edad (lógica simple para test)
    hoy = date.today()
    edad = hoy.year - fecha_nac.year - ((hoy.month, hoy.day) < (fecha_nac.month, fecha_nac.day))
    print(f"       Edad Calculada: {edad} años")

    # 2. Crear Turno con Médico Derivante (Simulando Router)
    print("\n2️⃣  Creando Turno con Médico Derivante Nuevo...")
    
    # Simular input del router: nombre del médico
    nombre_medico_input = "DR. HOUSE"
    
    # Lógica del router (simplificada)
    medico = db.query(MedicoDerivante).filter_by(nombre=nombre_medico_input).first()
    if not medico:
        print(f"    ℹ️  Médico '{nombre_medico_input}' no existe. Creando...")
        medico = MedicoDerivante(nombre=nombre_medico_input, matricula="M-555")
        db.add(medico)
        db.commit()
        db.refresh(medico)
    
    print(f"    ✅ Médico ID: {medico.id}")

    # Crear turno
    agenda = db.query(Agenda).first()
    turno = Turno(
        fecha=datetime.now() + timedelta(days=5),
        hora="11:00",
        duracion=20,
        paciente_id=paciente.id,
        agenda_id=agenda.id,
        medico_derivante_id=medico.id,
        estado="confirmado"
    )
    db.add(turno)
    db.commit()
    db.refresh(turno)

    print(f"    ✅ Turno creado ID: {turno.id}")
    print(f"       Médico Derivante Asociado: {turno.medico_derivante.nombre}")

    # Cleanup
    print("\n🧹 Limpiando datos de prueba...")
    db.delete(turno)
    db.delete(medico)
    db.delete(paciente)
    db.commit()
    print("✅ Limpieza completada.")
    db.close()

if __name__ == "__main__":
    test_enhancements()
