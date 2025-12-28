from database import SessionLocal
from models.user import User
from models.radioterapia import SeguimientoRadioterapia
from schemas.radioterapia import SeguimientoRadioterapiaCreate, SeguimientoRadioterapiaUpdate
from routers.radioterapia import create_registro, update_registro, list_registros
from datetime import date

def verify_radio():
    db = SessionLocal()
    try:
        user = db.query(User).first()
        current_user = {"id": user.id, "username": user.username, "role": user.role}
        print(f"Acting as {user.username}")
        
        # 1. Create
        print("Creating Registry...")
        payload = SeguimientoRadioterapiaCreate(
            paciente_id=9, # Use known patient ID
            patologia="TEST PATHOLOGY",
            medico_derivante="TEST DR",
            medico_responsable="Dra. Duarte",
            fecha_inicio=date.today()
        )
        reg = create_registro(payload, db, current_user)
        print(f"Created Registry ID: {reg.id}")
        
        # 2. List
        print("Listing Registries...")
        lst = list_registros(db=db, current_user=current_user)
        found = next((r for r in lst if r.id == reg.id), None)
        if not found:
            print("FAIL: Registry not found in list")
            return
        print(f"Found match: {found.patologia}")

        # 3. Update
        print("Updating Registry...")
        upd = SeguimientoRadioterapiaUpdate(observaciones="TEST OBS UPDATED")
        reg_updated = update_registro(reg.id, upd, db, current_user)
        print(f"Updated value: {reg_updated.observaciones}")
        if reg_updated.observaciones != "TEST OBS UPDATED":
            print("FAIL: Observaciones not updated")
            return

        print("Verification SUCCESS")

    except Exception as e:
        print(f"Verification FAILED: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    verify_radio()
