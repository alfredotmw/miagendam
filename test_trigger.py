from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "sqlite:///./agendas.db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db = SessionLocal()

def test_trigger():
    print("--- TESTING DB TRIGGER ---")
    try:
        # Note: We use patient_id=1, agenda_id=1, but a date/time that should fail
        # 1. Test 00:00:00
        print("Inserting 00:00:00...")
        db.execute(text("INSERT INTO turnos (fecha, hora, paciente_id, agenda_id, estado) VALUES ('2026-03-02 00:00:00', '00:00:00', 1, 1, 'PENDIENTE')"))
        db.commit()
        print("❌ Error: Trigger should have blocked 00:00:00")
    except Exception as e:
        print(f"✅ Success: Trigger blocked 00:00:00. Error: {e}")
        db.rollback()

    try:
        # 2. Test 23:00
        print("Inserting 23:00...")
        db.execute(text("INSERT INTO turnos (fecha, hora, paciente_id, agenda_id, estado) VALUES ('2026-03-02 23:00:00', '23:00', 1, 1, 'PENDIENTE')"))
        db.commit()
        print("❌ Error: Trigger should have blocked 23:00")
    except Exception as e:
        print(f"✅ Success: Trigger blocked 23:00. Error: {e}")
        db.rollback()

if __name__ == "__main__":
    test_trigger()
