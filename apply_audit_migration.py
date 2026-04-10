
import sqlite3
import os

def apply_migration():
    db_path = "agendas.db"
    if not os.path.exists(db_path):
        print(f"Error: {db_path} no encontrado.")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    tables_to_full_audit = ["turnos", "pacientes", "obras_sociales", "medicos_derivantes"]
    tables_to_partial_audit = ["seguimiento_radioterapia"]

    for table in tables_to_full_audit:
        print(f"Migrando tabla: {table}")
        try:
            cursor.execute(f"ALTER TABLE {table} ADD COLUMN creado_por_id INTEGER REFERENCES users(id)")
        except sqlite3.OperationalError as e:
            print(f"  Info: creado_por_id ya existe en {table} o error: {e}")
        
        try:
            cursor.execute(f"ALTER TABLE {table} ADD COLUMN fecha_creacion DATETIME")
        except sqlite3.OperationalError as e:
            print(f"  Info: fecha_creacion ya existe en {table} o error: {e}")
            
        try:
            cursor.execute(f"ALTER TABLE {table} ADD COLUMN modificado_por_id INTEGER REFERENCES users(id)")
        except sqlite3.OperationalError as e:
            print(f"  Info: modificado_por_id ya existe en {table} o error: {e}")
            
        try:
            cursor.execute(f"ALTER TABLE {table} ADD COLUMN fecha_modificacion DATETIME")
        except sqlite3.OperationalError as e:
            print(f"  Info: fecha_modificacion ya existe en {table} o error: {e}")

    for table in tables_to_partial_audit:
        print(f"Migrando tabla (parcial): {table}")
        try:
            cursor.execute(f"ALTER TABLE {table} ADD COLUMN creado_por_id INTEGER REFERENCES users(id)")
        except sqlite3.OperationalError as e:
            print(f"  Info: creado_por_id ya existe en {table} o error: {e}")
        
        try:
            cursor.execute(f"ALTER TABLE {table} ADD COLUMN modificado_por_id INTEGER REFERENCES users(id)")
        except sqlite3.OperationalError as e:
            print(f"  Info: modificado_por_id ya existe en {table} o error: {e}")

    conn.commit()
    conn.close()
    print("Migración de auditoría completada.")

if __name__ == "__main__":
    apply_migration()
