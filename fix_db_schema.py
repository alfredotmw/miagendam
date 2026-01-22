import sqlite3
import os

DB_PATH = "turnos.db" # Assuming this is the name, verify?

# Check actual DB name
if not os.path.exists(DB_PATH):
    # Try to find it
    files = [f for f in os.listdir(".") if f.endswith(".db")]
    if files:
        DB_PATH = files[0]
        print(f"Found DB: {DB_PATH}")
    else:
        print("No DB found!")
        exit(1)

def add_column():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        print("Attempting to add 'patologia' column to 'pacientes'...")
        cursor.execute("ALTER TABLE pacientes ADD COLUMN patologia TEXT")
        conn.commit()
        print("Success: Column added.")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print("Column already exists.")
        else:
            print(f"Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    add_column()
