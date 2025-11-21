import sqlite3

def add_column():
    conn = sqlite3.connect('agendas.db')
    cursor = conn.cursor()
    
    try:
        cursor.execute("ALTER TABLE turnos ADD COLUMN duracion INTEGER")
        conn.commit()
        print("✅ Columna 'duracion' agregada exitosamente.")
    except sqlite3.OperationalError as e:
        print(f"⚠️ Error (probablemente ya existe): {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    add_column()
