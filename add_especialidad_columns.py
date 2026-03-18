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
        # Check and add 'especialidad' to 'users'
        cursor.execute("PRAGMA table_info(users)")
        columns = [info[1] for info in cursor.fetchall()]
        if "especialidad" not in columns:
            cursor.execute("ALTER TABLE users ADD COLUMN especialidad VARCHAR")
            print("Added 'especialidad' to 'users' table.")
        else:
            print("'especialidad' already exists in 'users' table.")

        # Check and add 'especialidad_medico' to 'historia_clinica'
        cursor.execute("PRAGMA table_info(historia_clinica)")
        columns = [info[1] for info in cursor.fetchall()]
        if "especialidad_medico" not in columns:
            cursor.execute("ALTER TABLE historia_clinica ADD COLUMN especialidad_medico VARCHAR")
            print("Added 'especialidad_medico' to 'historia_clinica' table.")
        else:
            print("'especialidad_medico' already exists in 'historia_clinica' table.")

        conn.commit()
        print("Migration completed successfully.")

    except Exception as e:
        print(f"Error during migration: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
