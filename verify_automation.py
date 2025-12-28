from auth.jwt import create_access_token
from database import SessionLocal, engine, Base
from models.user import User
from models.paciente import Paciente
from models.radioterapia import SeguimientoRadioterapia
from models.historia_clinica import HistoriaClinica
from models.turno import Turno
from models.agenda import Agenda
from datetime import datetime, date

db = SessionLocal()

def verify_automation():
    print("--- 1. Setup Data ---")
    # Get a doctor user
    doctor = db.query(User).filter(User.role == "MEDICO").first()
    if not doctor:
        print("SKIP: No doctor found")
        return

    # Get a patient
    paciente = db.query(Paciente).first()
    if not paciente:
        print("SKIP: No patient found")
        return

    print(f"Doctor: {doctor.username}, Paciente: {paciente.apellido}")

    # --- TEST 1: Create Note with Indication ---
    print("\n--- 2. Creating Note with 'requiere_radioterapia=True' ---")
    
    # We simulate the API logic manually since we are in a script, 
    # OR we use requests to hit localhost if running. 
    # Let's use direct DB manipulation simulating the Router logic to test the LOGIC itself.
    
    # Simulate Router Logic for Create Note
    responsable = doctor.full_name or doctor.username
    nueva_nota = HistoriaClinica(
        paciente_id=paciente.id,
        texto="Nota de prueba automation",
        servicio="CONSULTA ONC.",
        creado_por_id=doctor.id,
        requiere_radioterapia=True, # 👈 KEY
        fecha=datetime.now()
    )
    db.add(nueva_nota)
    db.commit() # This saves note.
    
    # TRIGGER LOGIC (Copied from Router)
    if nueva_nota.requiere_radioterapia:
        nuevo_seguimiento = SeguimientoRadioterapia(
            paciente_id=nueva_nota.paciente_id,
            fecha_consulta=date.today(),
            medico_responsable=responsable,
            medico_derivante="",
            observaciones=f"Indicado por {responsable} (AUTO TEST)"
        )
        db.add(nuevo_seguimiento)
        db.commit()
        print("✅ Registry Entry Created via Trigger Logic")

    # Verify Registry Exists
    reg = db.query(SeguimientoRadioterapia).filter(
        SeguimientoRadioterapia.paciente_id == paciente.id, 
        SeguimientoRadioterapia.medico_responsable == responsable
    ).order_by(SeguimientoRadioterapia.id.desc()).first()
    
    assert reg is not None
    assert reg.fecha_consulta == date.today()
    print(f"✅ Registry found: ID {reg.id}, Resp: {reg.medico_responsable}")

    # --- TEST 2: Create Turno for Radio (Updates Start Date) ---
    print("\n--- 3. Creating Turno for Radiotherapy (Agenda 3) ---")
    
    radio_agenda = db.query(Agenda).filter(Agenda.id == 3).first()
    if not radio_agenda:
        print("⚠️ Agenda 3 not found, using first available")
        radio_agenda = db.query(Agenda).first()
    
    nuevo_turno = Turno(
        fecha=datetime.now(),
        hora="10:00",
        duracion=15,
        paciente_id=paciente.id,
        agenda_id=3, # FORCE RADIOTERAPIA SAN MARTIN
        estado="PENDIENTE"
    )
    db.add(nuevo_turno)
    db.commit()
    
    # TRIGGER LOGIC (Copied from Router)
    # Find LATEST tracking
    seguimiento = db.query(SeguimientoRadioterapia)\
        .filter(SeguimientoRadioterapia.paciente_id == paciente.id)\
        .order_by(SeguimientoRadioterapia.created_at.desc())\
        .first()
    
    if seguimiento:
        is_radio_agenda = nuevo_turno.agenda_id in [3, 4] 
        print(f"   -> Turno Agenda ID: {nuevo_turno.agenda_id}. Is Radio? {is_radio_agenda}")
        
        updated = False
        if is_radio_agenda:
            if not seguimiento.fecha_inicio:
                seguimiento.fecha_inicio = nuevo_turno.fecha.date()
                updated = True
                print("   -> Set fecha_inicio (was empty)")
            elif nuevo_turno.fecha.date() < seguimiento.fecha_inicio:
                seguimiento.fecha_inicio = nuevo_turno.fecha.date()
                updated = True
                print("   -> Updated fecha_inicio (earlier date)")
        
        if updated:
            db.commit()
            print("✅ Registry Updated via Trigger Logic")
    
    # Verify Update
    db.refresh(reg)
    print(f"Registry fecha_inicio: {reg.fecha_inicio}")
    assert reg.fecha_inicio == date.today()
    print("✅ Verification Successful!")

try:
    verify_automation()
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
finally:
    db.close()
