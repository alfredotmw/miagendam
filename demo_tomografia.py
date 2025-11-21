from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from database import SessionLocal
from models.agenda import Agenda
from models.practica import Practica
from models.paciente import Paciente
from models.turno import Turno
from models.turno_practica import TurnoPractica
from services.turno_service import calculate_duration, check_availability

def demo_tomo():
    db = SessionLocal()
    print("🏥 --- DEMO: Creación de Turno de Tomografía ---\n")

    # 1. Obtener Datos Necesarios
    agenda = db.query(Agenda).filter_by(nombre="TOMOGRAFIAS Y RX").first()
    practica = db.query(Practica).filter_by(nombre="TAC DE CEREBRO").first()
    
    # Crear un paciente dummy si no hay
    paciente = db.query(Paciente).first()
    if not paciente:
        paciente = Paciente(nombre="Juan", apellido="Perez", dni="12345678", telefono="123", email="juan@test.com")
        db.add(paciente)
        db.commit()
        db.refresh(paciente)

    print(f"1️⃣  Datos seleccionados:")
    print(f"    Agenda: {agenda.nombre} (ID: {agenda.id})")
    print(f"    Práctica: {practica.nombre} (ID: {practica.id})")
    print(f"    Paciente: {paciente.nombre} {paciente.apellido}\n")

    # 2. Simular Payload del Frontend (lo que envía el usuario)
    fecha_turno = datetime.now().replace(hour=10, minute=0, second=0, microsecond=0) + timedelta(days=2)
    print(f"2️⃣  Intentando crear turno para: {fecha_turno}")
    print(f"    Prácticas solicitadas: [{practica.nombre}]")

    # 3. Lógica del Backend (lo que hicimos recién)
    print("\n3️⃣  Procesando lógica de negocio...")
    
    # Calcular duración
    duracion = calculate_duration(agenda.tipo, [practica])
    print(f"    ✅ Duración calculada: {duracion} minutos (Regla: Tomografía = 20 min)")

    # Verificar disponibilidad
    try:
        check_availability(db, agenda.id, fecha_turno, duracion, agenda.tipo)
        print("    ✅ Disponibilidad: OK")
    except Exception as e:
        print(f"    ❌ Error de disponibilidad: {e}")
        return

    # 4. Guardar Turno
    nuevo_turno = Turno(
        fecha=fecha_turno,
        hora=fecha_turno.strftime("%H:%M"),
        duracion=duracion,
        paciente_id=paciente.id,
        agenda_id=agenda.id,
        estado="confirmado"
    )
    db.add(nuevo_turno)
    db.flush()
    
    # Asociar práctica
    tp = TurnoPractica(turno_id=nuevo_turno.id, practica_id=practica.id)
    db.add(tp)
    db.commit()
    
    print(f"\n✅ Turno creado exitosamente con ID: {nuevo_turno.id}")

    # 5. Mostrar "Vista de Agenda"
    print("\n📅 --- VISTA DE AGENDA (TOMOGRAFIAS Y RX) ---")
    print(f"Fecha: {fecha_turno.date()}\n")
    print(f"{'HORA':<10} | {'PACIENTE':<20} | {'PRACTICA':<20} | {'DURACION':<10}")
    print("-" * 70)

    turnos_del_dia = db.query(Turno).filter(
        Turno.agenda_id == agenda.id,
        # Filtro simple por día (en prod usaríamos rangos de fecha)
    ).all()

    # Filtrar en python por el día exacto para la demo
    turnos_del_dia = [t for t in turnos_del_dia if t.fecha.date() == fecha_turno.date()]

    for t in turnos_del_dia:
        practica_nombre = t.practica[0].nombre if t.practica else "Varios" # Ojo: t.practica es una lista si usaste relationship many-to-many o similar, pero en tu modelo Turno tiene 'practica' relationship directo? 
        # Revisando modelo Turno: practica = relationship("Practica")... espera, Turno tiene practica_id (FK) pero también creamos TurnoPractica (Many-to-Many).
        # En el router guardamos en TurnoPractica.
        # El modelo Turno tiene `practica_id` (singular) que parece ser legacy o principal, y `practica` relationship.
        # Pero en el router NO llenamos `practica_id` en el objeto Turno? 
        # Revisemos router: `nuevo_turno = Turno(..., practica_id=???)` -> NO, el router NO guarda practica_id en Turno, solo en TurnoPractica.
        # PERO el modelo Turno TIENE `practica_id = Column(..., nullable=True)`.
        # Y `practica = relationship(...)`.
        # Si no llenamos practica_id, `t.practica` será None.
        # Deberíamos acceder a las prácticas via la tabla intermedia, pero Turno no tiene definida la relación `practicas` (plural) hacia TurnoPractica o secondary.
        
        # Para la demo, voy a hacer un query manual de las prácticas del turno para mostrarlo bien.
        practicas_del_turno = db.query(Practica).join(TurnoPractica).filter(TurnoPractica.turno_id == t.id).all()
        nombres_practicas = ", ".join([p.nombre for p in practicas_del_turno])

        print(f"{t.hora:<10} | {t.paciente.apellido}, {t.paciente.nombre[0]}.{'':<5} | {nombres_practicas[:18]:<20} | {t.duracion} min")

    print("-" * 70)
    db.close()

if __name__ == "__main__":
    demo_tomo()
