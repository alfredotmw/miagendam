from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "sqlite:///./agendas.db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db = SessionLocal()

def apply_blindage():
    print("--- APPLYING DATABASE BLINDAGE ---")
    
    # 1. UNIQUE INDEX on turnos (agenda_id, paciente_id, fecha)
    # This prevents the exact same patient/agenda/timestamp duplication.
    print("1. Creating UNIQUE index on turnos(agenda_id, paciente_id, fecha)...")
    try:
        db.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS idx_unique_turno ON turnos(agenda_id, paciente_id, fecha)"))
        db.commit()
        print("✅ Unique index created.")
    except Exception as e:
        db.rollback()
        print(f"❌ Error creating unique index: {e}")

    # 2. TRIGGER for Business Hours (07:00-21:00)
    # This is better than CHECK for SQLite ALTER limitations.
    print("2. Creating TRIGGER for business hours validation...")
    try:
        # Trigger on INSERT
        db.execute(text("""
            CREATE TRIGGER IF NOT EXISTS validate_hour_insert
            BEFORE INSERT ON turnos
            FOR EACH ROW
            BEGIN
                SELECT CASE
                    WHEN NEW.hora LIKE '00:00%' THEN
                        RAISE(ABORT, '⚠️ Horario no habilitado (00:00 es inválido)')
                    WHEN CAST(STRFTIME('%H', NEW.fecha) AS INTEGER) < 7 OR CAST(STRFTIME('%H', NEW.fecha) AS INTEGER) >= 21 THEN
                        RAISE(ABORT, '⚠️ Horario no habilitado (Rango permitido: 07:00–21:00)')
                END;
            END;
        """))
        # Trigger on UPDATE
        db.execute(text("""
            CREATE TRIGGER IF NOT EXISTS validate_hour_update
            BEFORE UPDATE ON turnos
            FOR EACH ROW
            WHEN NEW.fecha != OLD.fecha OR NEW.hora != OLD.hora
            BEGIN
                SELECT CASE
                    WHEN NEW.hora LIKE '00:00%' THEN
                        RAISE(ABORT, '⚠️ Horario no habilitado (00:00 es inválido)')
                    WHEN CAST(STRFTIME('%H', NEW.fecha) AS INTEGER) < 7 OR CAST(STRFTIME('%H', NEW.fecha) AS INTEGER) >= 21 THEN
                        RAISE(ABORT, '⚠️ Horario no habilitado (Rango permitido: 07:00–21:00)')
                END;
            END;
        """))
        db.commit()
        print("✅ Business hours triggers created.")
    except Exception as e:
        db.rollback()
        print(f"❌ Error creating triggers: {e}")

    print("--- BLINDAGE FINISHED ---")

if __name__ == "__main__":
    apply_blindage()
