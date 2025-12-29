from database import SessionLocal
from models.user import User
from models.historia_clinica import HistoriaClinica
from models.radioterapia import SeguimientoRadioterapia
from models.turno import Turno
from models.agenda import Agenda
from models.practica import Practica
from routers.historia_clinica import crear_nota
from routers.radioterapia import list_registros
from schemas.historia_clinica import HistoriaClinicaCreate
from datetime import datetime, date, timedelta

def verify_automation():
    db = SessionLocal()
    try:
        print("--- SETUP ---")
        # 0. Get User and Patient
        user = db.query(User).filter(User.role == "MEDICO").first()
        if not user:
            user = db.query(User).first() # Fallback
        
        current_user = {"id": user.id, "username": user.username, "role": user.role, "full_name": user.full_name}
        print(f"User: {current_user['username']}")

        # Clean existing test data for patient 9
        PID = 9
        db.query(SeguimientoRadioterapia).filter(SeguimientoRadioterapia.paciente_id == PID).delete()
        db.query(Turno).filter(Turno.paciente_id == PID).delete() # 👈 Clean Turnos
        db.commit()
        print("Cleaned old records")

        print("\n--- STEP 1: CREATE CLINICAL HISTORY (Trigger) ---")
        note_data = HistoriaClinicaCreate(
            paciente_id=PID,
            servicio="ONCOLOGIA",
            texto="Paciente requiere inicio de tratamiento.",
            requiere_radioterapia=True, # <--- TRIGGER
            diagnostico_diferencial="Ca. Mama",
            estadio="IIA",
            accion="GUARDAR"
        )
        
        # Call the router function directly
        crear_nota(note_data, db, current_user)
        print("Note Created.")
        
        # Verify creation
        reg = db.query(SeguimientoRadioterapia).filter(SeguimientoRadioterapia.paciente_id == PID).first()
        if not reg:
            print("❌ FAIL: Radiotherapy Registry NOT created.")
            return
        print(f"✅ SUCCESS: Registry created. ID: {reg.id}, Path: {reg.patologia}")

        print("\n--- STEP 2: CREATE APPOINTMENTS (Dates Source) ---")
        # Create Agenda Types if needed (assuming they exist or using raw strings)
        # Ensure we have a TOMOGRAFIA agenda/practice
        
        # Create a TOMOGRAFIA appointment (simulate usage)
        # We need an agenda.
        agenda_tomo = db.query(Agenda).filter(Agenda.tipo == "TOMOGRAFIA").first()
        if not agenda_tomo:
            print("Creating Mock TOMO Agenda")
            agenda_tomo = Agenda(nombre="TOMO TEST", tipo="TOMOGRAFIA")
            db.add(agenda_tomo)
            db.commit()
            
        # 🟢 Create and Assign Medico Derivante
        from models.medico import MedicoDerivante
        derivante = db.query(MedicoDerivante).filter(MedicoDerivante.nombre == "JUAN DERIVANTE").first()
        if not derivante:
            derivante = MedicoDerivante(nombre="JUAN DERIVANTE", matricula="111")
            db.add(derivante)
            db.commit()
            
        tomo_date = datetime.now() - timedelta(days=5)
        t1 = Turno(
            paciente_id=PID,
            agenda_id=agenda_tomo.id,
            fecha=tomo_date,
            hora="10:00",
            estado="COMPLETADO",
            medico_derivante_id=derivante.id # Assign!
        )
        db.add(t1)
        
        # Create RADIOTERAPIA appointment (Start)
        agenda_radio = db.query(Agenda).filter(Agenda.tipo == "RADIOTERAPIA").first()
        if not agenda_radio:
            print("Creating Mock RADIO Agenda")
            agenda_radio = Agenda(nombre="RADIO TEST", tipo="RADIOTERAPIA")
            db.add(agenda_radio)
            db.commit()
            
        start_date = datetime.now() + timedelta(days=2)
        t2 = Turno(
            paciente_id=PID,
            agenda_id=agenda_radio.id,
            fecha=start_date,
            hora="08:00",
            estado="PENDIENTE"
        )
        db.add(t2)
        
        db.commit()
        print("Appointments Created.")

        print("\n--- STEP 3: LIST REGISTRIES (Trigger Auto-fill) ---")
        # Function triggers check_and_autofill
        results = list_registros(db=db, current_user=current_user, limit=10)
        
        my_reg = next((r for r in results if r.id == reg.id), None)
        
        print(f"Results: TAC={my_reg.fecha_tac}, INICIO={my_reg.fecha_inicio}")
        
        if my_reg.fecha_tac == tomo_date.date() and my_reg.fecha_inicio == start_date.date():
             print("✅ SUCCESS: Dates Auto-filled correctly.")
        else:
             print(f"❌ FAIL: Dates mismatch. Expected {tomo_date.date()} & {start_date.date()}")

        # Check Names
        print(f"Responsable In DB: {my_reg.medico_responsable}")
        print(f"Derivante In DB: {my_reg.medico_derivante}")
        
        if "JUAN DERIVANTE" in my_reg.medico_derivante:
             print("✅ SUCCESS: Derivante detected correctly.")
        else:
             print("❌ FAIL: Derivante NOT detected.")

    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    verify_automation()
