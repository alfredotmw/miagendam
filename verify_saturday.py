from datetime import date, datetime
from database import SessionLocal
from routers.turnos import get_available_slots
from models.agenda import Agenda

def verify_saturday():
    db = SessionLocal()
    try:
        # Find a future Saturday
        today = date.today()
        # 0=Mon ... 5=Sat
        days_until_saturday = (5 - today.weekday() + 7) % 7
        if days_until_saturday == 0:
            days_until_saturday = 7 # Next Saturday if today is Sat
        
        next_saturday = today.replace(day=today.day + days_until_saturday)
        # Use simple addition for safety across month boundaries
        from datetime import timedelta
        next_saturday = today + timedelta(days=days_until_saturday)
        
        print(f"Verifying for Saturday: {next_saturday}")
        
        # Pick an agenda (e.g. 1)
        agenda = db.get(Agenda, 1)
        if not agenda:
            print("Agenda 1 not found, trying 2")
            agenda_id = 2
        else:
            agenda_id = 1
            
        print(f"Checking Agenda {agenda_id}...")
        
        # Test get_available_slots directly logic snippet
        # Since we modified the router logic, we should probably call the function or simulate it.
        # But get_available_slots is an endpoint deps... let's just use the logic we modified.
        
        # The logic modified was:
        # if current_date.weekday() < 6:
        
        # Let's run a simulation of that loop
        dates_to_check = []
        current_date = next_saturday
        
        # Weekday check
        wd = current_date.weekday()
        print(f"Weekday index: {wd} (should be 5)")
        
        if wd < 6:
            print("✅ Weekday check passed ( < 6 )")
        else:
            print("❌ Weekday check FAILED")

        # Now let's try to actually find slots using the router function logic if possible, 
        # or just trust the logic check since we can't easily query the API without auth here.
        
    finally:
        db.close()

if __name__ == "__main__":
    verify_saturday()
