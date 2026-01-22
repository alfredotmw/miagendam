from database import SessionLocal
from routers.analytics import get_dashboard_data, normalize_service
from models.radioterapia import SeguimientoRadioterapia
from sqlalchemy.orm import Session

def test_analytics():
    db = SessionLocal()
    try:
        print("Testing normalize_service...")
        print(normalize_service("QUIMIOTERAPIA SAN MARTIN"))
        print(normalize_service("RADIOTERAPIA (LINAC) - COLOMBIA"))
        
        print("Testing Dashboard Data Aggregation...")
        
        # Mocking current_user
        data = get_dashboard_data(start_date=None, end_date=None, db=db, current_user={"role": "ADMIN"})
        
        print("Keys returned:", data.keys())
        if "radiotherapy" in data:
            print("Radiotherapy Stats keys:", data["radiotherapy"].keys())
            sm = data["radiotherapy"]["SAN MARTIN"]
            print("SM Keys:", sm.keys())
            # Check if patient relation works in agg
            print("SM Patologias:", sm.get("patologias"))
            print("SM Trends:", sm.get("trends"))
        
        print("Success!")
    except Exception as e:
        print("CRASHED:")
        print(e)
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    test_analytics()
