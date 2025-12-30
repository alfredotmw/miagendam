from database import SessionLocal, engine
from sqlalchemy import text

def add_columns():
    db = SessionLocal()
    try:
        # Check if columns exist
        with engine.connect() as connection:
            result = connection.execute(text("PRAGMA table_info(seguimiento_radioterapia)"))
            columns = [row[1] for row in result]
            
            if "sede" not in columns:
                print("Adding 'sede' column...")
                connection.execute(text("ALTER TABLE seguimiento_radioterapia ADD COLUMN sede VARCHAR"))
            else:
                print("'sede' column already exists.")
                
            if "tipo_tecnica" not in columns:
                print("Adding 'tipo_tecnica' column...")
                connection.execute(text("ALTER TABLE seguimiento_radioterapia ADD COLUMN tipo_tecnica VARCHAR"))
            else:
                print("'tipo_tecnica' column already exists.")
                
            connection.commit()
            print("Migration completed successfully.")
            
    except Exception as e:
        print(f"Error migrating database: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    add_columns()
