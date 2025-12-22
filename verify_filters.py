from database import SessionLocal
from routers.historia_clinica import get_timeline_by_dni
from datetime import date, timedelta

def test_filters():
    db = SessionLocal()
    try:
        # Use the test patient from before (DNI: TEST_HISTORIA)
        # Assuming we have data. If not, this might fail if patient doesn't exist, but we created it in previous step.
        dni = "TEST_HISTORIA"
        
        print(f"Testing timeline for DNI: {dni}")
        
        # Test 1: No filters
        resp = get_timeline_by_dni(dni, db=db)
        print(f"Total items (No filter): {len(resp.timeline)}")
        print(f"Patient Name: {resp.paciente.nombre} {resp.paciente.apellido}")
        
        # Test 2: Date filter (Future date -> Should get 0)
        future_start = date.today() + timedelta(days=365)
        resp_future = get_timeline_by_dni(dni, start_date=future_start, db=db)
        print(f"Total items (Future filter): {len(resp_future.timeline)}")

        # Test 3: Date filter (Today -> Should get items)
        today = date.today()
        resp_today = get_timeline_by_dni(dni, start_date=today, end_date=today, db=db)
        print(f"Total items (Today filter): {len(resp_today.timeline)}")

        if len(resp.timeline) > 0 and len(resp_future.timeline) == 0:
            print("VERIFICATION SUCCESS: Filters working correctly.")
        else:
            print("VERIFICATION WARNING: Check output logic.")

    except Exception as e:
        print(f"Verification FAILED: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    test_filters()
