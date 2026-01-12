from database import SessionLocal, engine
from sqlalchemy import text

def add_medico_column():
    db = SessionLocal()
    try:
        # SQLite way to check columns
        result = db.execute(text("PRAGMA table_info(pacientes)"))
        columns = [row[1] for row in result.fetchall()]
        
        if 'medico_derivante_id' in columns:
            print("Columna 'medico_derivante_id' ya existe.")
        else:
            print("Agregando columna 'medico_derivante_id'...")
            db.execute(text("ALTER TABLE pacientes ADD COLUMN medico_derivante_id INTEGER REFERENCES medicos_derivantes(id)"))
            db.commit()
            print("Columna agregada exitosamente.")
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    add_medico_column()
