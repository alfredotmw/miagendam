import sqlite3

def update_schema():
    conn = sqlite3.connect('agendas.db')
    cursor = conn.cursor()
    
    print("🔄 Actualizando esquema de base de datos...")

    # 1. Tabla Pacientes
    try:
        cursor.execute("ALTER TABLE pacientes ADD COLUMN sexo VARCHAR")
        print("   ✅ Columna 'sexo' agregada a 'pacientes'.")
    except sqlite3.OperationalError:
        print("   ⚠️ Columna 'sexo' ya existe en 'pacientes'.")

    try:
        cursor.execute("ALTER TABLE pacientes ADD COLUMN celular VARCHAR")
        print("   ✅ Columna 'celular' agregada a 'pacientes'.")
    except sqlite3.OperationalError:
        print("   ⚠️ Columna 'celular' ya existe en 'pacientes'.")

    # 2. Tabla Medicos Derivantes (Nueva)
    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS medicos_derivantes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre VARCHAR NOT NULL UNIQUE,
                matricula VARCHAR,
                telefono VARCHAR,
                email VARCHAR
            )
        """)
        print("   ✅ Tabla 'medicos_derivantes' creada/verificada.")
    except sqlite3.OperationalError as e:
        print(f"   ❌ Error creando tabla 'medicos_derivantes': {e}")

    # 3. Tabla Turnos (FK a Medico)
    try:
        cursor.execute("ALTER TABLE turnos ADD COLUMN medico_derivante_id INTEGER REFERENCES medicos_derivantes(id)")
        print("   ✅ Columna 'medico_derivante_id' agregada a 'turnos'.")
    except sqlite3.OperationalError:
        print("   ⚠️ Columna 'medico_derivante_id' ya existe en 'turnos'.")

    conn.commit()
    conn.close()
    print("✅ Actualización de esquema finalizada.")

if __name__ == "__main__":
    update_schema()
