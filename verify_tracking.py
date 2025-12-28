from database import SessionLocal
from models.paciente import Paciente
from models.user import User
from schemas.historia_clinica import HistoriaClinicaCreate
from models.historia_clinica import HistoriaClinica
from routers.historia_clinica import crear_nota, update_nota, get_timeline
from datetime import datetime

def verify_tracking():
    db = SessionLocal()
    try:
        # 1. Setup User
        user = db.query(User).filter(User.username == "admin").first()
        if not user:
            print("Admin user not found, using first user")
            user = db.query(User).first()
        
        current_user_dict = {"id": user.id, "username": user.username, "role": user.role, "allowed_agendas": ""}
        print(f"Acting as user: {user.username} (ID: {user.id})")

        # 2. Setup Patient
        p = db.query(Paciente).filter(Paciente.dni == "TEST_TRACKING").first()
        if not p:
            p = Paciente(nombre="Tracking", apellido="Test", dni="TEST_TRACKING")
            db.add(p)
            db.commit()
            db.refresh(p)
        print(f"Patient ID: {p.id}")

        # 3. Create Note (Simulate Router)
        print("Creating note...")
        payload = HistoriaClinicaCreate(
            paciente_id=p.id,
            servicio="TEST_SRV",
            texto="Note created for tracking test",
            accion="GUARDAR"
        )
        
        # Call router function directly
        note_out = crear_nota(payload, db, current_user_dict)
        print(f"Note Created. ID: {note_out.id}")
        
        # Verify DB content
        if note_out.creado_por_id != user.id:
            print(f"FAIL: creado_por_id mismatch. Expected {user.id}, got {note_out.creado_por_id}")
            return

        # 4. Fetch Timeline
        print("Fetching timeline...")
        timeline_res = get_timeline(p.id, start_date=None, end_date=None, db=db, current_user=current_user_dict)
        
        # Find our note
        event = next((e for e in timeline_res.timeline if e.id_referencia == note_out.id and e.tipo == "NOTA"), None)
        if not event:
            print("FAIL: Note event not found in timeline")
            return
            
        print(f"Timeline Event Found: {event.descripcion}")
        print(f" - Creado por: {event.creado_por}")
        
        if event.creado_por is None:
             print("FAIL: 'creado_por' is None. Relationship not loading?")
             # Debug relationship
             db_note = db.query(HistoriaClinica).get(note_out.id)
             print(f"DEBUG: note.creado_por_id = {db_note.creado_por_id}")
             print(f"DEBUG: note.creado_por = {db_note.creado_por}")
             return

        if event.creado_por != user.full_name and event.creado_por != user.username:
             print(f"FAIL: 'creado_por' field not matching user name/username. Got: {event.creado_por}")
             return

        # 5. Edit Note (Simulate Router)
        print("Editing note...")
        update_payload = HistoriaClinicaCreate(
             paciente_id=p.id,
             servicio="TEST_SRV",
             texto="Note UPDATED for tracking test",
             accion="GUARDAR"
        )
        # Assuming we can update (checks signature etc)
        updated_note = update_nota(note_out.id, update_payload, db, current_user_dict)
        
        # 6. Fetch Timeline Again relative
        timeline_res_2 = get_timeline(p.id, db=db, current_user=current_user_dict)
        event_2 = next((e for e in timeline_res_2.timeline if e.id_referencia == note_out.id), None)
        
        print(f" - Editado por: {event_2.editado_por}")
        if event_2.editado_por != user.full_name and event_2.editado_por != user.username:
             print(f"FAIL: 'editado_por' field not matching. Got: {event_2.editado_por}")
             return

        print("Verification SUCCESS: User tracking fields are working.")

    except Exception as e:
        print(f"Verification FAILED: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    verify_tracking()
