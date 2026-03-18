import sqlite3
import os

DB_PATH = "agendas.db"

def migrate():
    if not os.path.exists(DB_PATH):
        print(f"Error: {DB_PATH} not found.")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # Check and add 'tipo_evolucion' to 'historia_clinica'
        cursor.execute("PRAGMA table_info(historia_clinica)")
        columns = [info[1] for info in cursor.fetchall()]
        if "tipo_evolucion" not in columns:
            cursor.execute("ALTER TABLE historia_clinica ADD COLUMN tipo_evolucion VARCHAR")
            
            # Backfill existing data
            cursor.execute("UPDATE historia_clinica SET tipo_evolucion = 'oncologia' WHERE tipo_evolucion IS NULL")
            print("Added 'tipo_evolucion' to 'historia_clinica' table and backfilled existing records.")
        else:
            print("'tipo_evolucion' already exists in 'historia_clinica' table.")

        conn.commit()
        print("Migration completed successfully.")

    except Exception as e:
        print(f"Error during migration: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
