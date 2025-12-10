import sqlite3

def add_patologia_column():
    db_path = 'agendas.db'
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if column exists
        cursor.execute("PRAGMA table_info(turnos)")
        columns = [info[1] for info in cursor.fetchall()]
        
        if 'patologia' not in columns:
            print("Adding 'patologia' column to 'turnos' table...")
            cursor.execute("ALTER TABLE turnos ADD COLUMN patologia VARCHAR")
            conn.commit()
            print("Column added successfully.")
        else:
            print("'patologia' column already exists.")
            
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    add_patologia_column()
