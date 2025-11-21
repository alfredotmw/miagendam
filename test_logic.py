from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from database import SessionLocal
from models.practica import Practica, CategoriaPractica
from models.agenda import Agenda
from models.turno import Turno
from services.turno_service import calculate_duration, check_availability
from fastapi import HTTPException

def test_logic():
    db = SessionLocal()
    print("🧪 Probando Lógica de Turnos...")

    # 1. Test Duración Tomografía (20 min)
    print("\n--- Test 1: Duración Tomografía ---")
    practicas_tomo = [Practica(nombre="TAC CEREBRO", categoria=CategoriaPractica.TOMOGRAFIA)]
    duracion = calculate_duration("TOMOGRAFIA", practicas_tomo)
    print(f"Esperado: 20, Obtenido: {duracion}")
    assert duracion == 20

    # 2. Test Duración RX (15 min)
    print("\n--- Test 2: Duración RX ---")
    practicas_rx = [Practica(nombre="RX TORAX", categoria=CategoriaPractica.RADIOGRAFIA)]
    duracion = calculate_duration("TOMOGRAFIA", practicas_rx) # Agenda mixta
    print(f"Esperado: 15, Obtenido: {duracion}")
    assert duracion == 15

    # 3. Test Duración Mixta (30 min)
    print("\n--- Test 3: Duración Mixta (Tomo + RX) ---")
    practicas_mixtas = [
        Practica(nombre="TAC CEREBRO", categoria=CategoriaPractica.TOMOGRAFIA),
        Practica(nombre="RX TORAX", categoria=CategoriaPractica.RADIOGRAFIA)
    ]
    duracion = calculate_duration("TOMOGRAFIA", practicas_mixtas)
    print(f"Esperado: 30, Obtenido: {duracion}")
    assert duracion == 30

    # 4. Test Radioterapia Custom
    print("\n--- Test 4: Radioterapia Custom ---")
    try:
        calculate_duration("RADIOTERAPIA", [], custom_duration=15)
        print("❌ Error: Debería haber fallado con 15 min")
    except HTTPException as e:
        print(f"✅ Correcto: Falló con 15 min ({e.detail})")
    
    duracion = calculate_duration("RADIOTERAPIA", [], custom_duration=20)
    print(f"Esperado: 20, Obtenido: {duracion}")
    assert duracion == 20

    # 5. Test Disponibilidad Quimioterapia (Capacidad 7)
    print("\n--- Test 5: Capacidad Quimioterapia ---")
    
    # Usar una nueva sesión para esta parte para evitar conflictos
    db.close()
    db = SessionLocal()

    agenda_quimio = db.query(Agenda).filter_by(tipo="QUIMIOTERAPIA").first()
    if not agenda_quimio:
        print("⚠️ No se encontró agenda de Quimioterapia para el test.")
        return

    fecha_base = datetime.now().replace(minute=0, second=0, microsecond=0) + timedelta(days=1)
    
    print(f"Usando Agenda: {agenda_quimio.nombre}")
    
    turnos_ids = []
    try:
        for i in range(7):
            t = Turno(
                fecha=fecha_base, 
                hora="09:00", 
                duracion=60, 
                paciente_id=1, # Asumiendo ID 1 existe
                agenda_id=agenda_quimio.id,
                estado="pendiente"
            )
            db.add(t)
            db.commit()
            db.refresh(t)
            turnos_ids.append(t.id)

        # Intentar reservar el 8vo turno
        try:
            check_availability(db, agenda_quimio.id, fecha_base, 60, "QUIMIOTERAPIA")
            print("❌ Error: Debería haber fallado por capacidad completa")
        except HTTPException as e:
            print(f"✅ Correcto: Bloqueado por capacidad ({e.detail})")

    except Exception as e:
        print(f"❌ Error inesperado durante el test: {e}")
    finally:
        # Cleanup usando IDs
        print("🧹 Limpiando turnos de prueba...")
        for t_id in turnos_ids:
            t_db = db.get(Turno, t_id)
            if t_db:
                db.delete(t_db)
        db.commit()
        print("✅ Limpieza completada.")

    db.close()

if __name__ == "__main__":
    test_logic()
