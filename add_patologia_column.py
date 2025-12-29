from database import SessionLocal, engine
from sqlalchemy import text

def add_patologia_column():
    db = SessionLocal()
    try:
        # SQLite way to check columns
        result = db.execute(text("PRAGMA table_info(historia_clinica)"))
        columns = [row[1] for row in result.fetchall()]
        
        if 'patologia' in columns:
            print("Columna 'patologia' ya existe.")
        else:
            print("Agregando columna 'patologia'...")
            db.execute(text("ALTER TABLE historia_clinica ADD COLUMN patologia TEXT"))
            db.commit()
            print("Columna agregada exitosamente.")
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    add_patologia_column()
