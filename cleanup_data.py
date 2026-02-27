from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "sqlite:///./agendas.db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db = SessionLocal()

def cleanup():
    print("--- STARTING DATA CLEANUP (RETRY) ---")
    
    # 1. DELETE 00:00:00 appointments
    print("1. Deleting appointments with hora = '00:00:00' or '00:00'...")
    try:
        # We try to be more flexible with the time string
        res = db.execute(text("DELETE FROM turnos WHERE hora LIKE '00:00%'"))
        count = res.rowcount
        db.commit()
        print(f"✅ Deleted {count} appointments with invalid time.")
    except Exception as e:
        db.rollback()
        print(f"❌ Error deleting invalid times: {e}")

    # 2. DELETE Duplicates (same agenda_id, paciente_id, practica_id, fecha [date part])
    print("2. Detecting and deleting duplicates (same patient, agenda, practice, day)...")
    try:
        # Logic: Select turnos that are duplicates of an older turno (smaller ID)
        find_dupes_query = text("""
            SELECT t1.id
            FROM turnos t1
            JOIN turnos_practicas tp1 ON t1.id = tp1.turno_id
            WHERE EXISTS (
                SELECT 1 FROM turnos t2
                JOIN turnos_practicas tp2 ON t2.id = tp2.turno_id
                WHERE t1.id > t2.id
                AND t1.agenda_id = t2.agenda_id
                AND t1.paciente_id = t2.paciente_id
                AND DATE(t1.fecha) = DATE(t2.fecha)
                AND tp1.practica_id = tp2.practica_id
                AND t1.estado != 'cancelado' 
                AND t2.estado != 'cancelado'
            )
        """)
        
        dupe_ids = [r[0] for r in db.execute(find_dupes_query).fetchall()]
        if dupe_ids:
            print(f"⚠️ Found {len(dupe_ids)} duplicate records. IDs: {dupe_ids}")
            
            # Delete from association table first
            for tid in dupe_ids:
                db.execute(text("DELETE FROM turnos_practicas WHERE turno_id = :tid"), {"tid": tid})
                db.execute(text("DELETE FROM turnos WHERE id = :tid"), {"tid": tid})
            
            db.commit()
            print(f"✅ Deleted {len(dupe_ids)} duplicate turnos.")
        else:
            print("✅ No duplicates found.")

    except Exception as e:
        db.rollback()
        print(f"❌ Error deleting duplicates: {e}")

    print("--- CLEANUP FINISHED ---")

if __name__ == "__main__":
    cleanup()
