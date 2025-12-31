from database import SessionLocal
from models.radioterapia import SeguimientoRadioterapia
from schemas.radioterapia import SeguimientoRadioterapiaOut as SchemaRadio
from routers.radioterapia import listar_seguimientos

def check_endpoint():
    db = SessionLocal()
    print("Checking /radioterapia/ endpoint logic...")
    try:
        # Simulate request
        results = listar_seguimientos(db=db, current_user={"username": "admin"})
        print(f"Endpoint returned {len(results)} items.")
        for item in results:
            # Validate schema conversion
            # If this crashes, then the endpoint is broken due to Schema mismatch with DB model
            print(f"Item {item.id} - Sede: {item.sede}, Tec: {item.tipo_tecnica}")
            
        print("Endpoint check PASSED.")
    except Exception as e:
        print(f"Endpoint CRASHED: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_endpoint()
