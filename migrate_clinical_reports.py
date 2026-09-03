# migrate_clinical_reports.py

import sys
from database import engine
from sqlalchemy import text, inspect

def up():
    inspector = inspect(engine)
    if not inspector.has_table("informes_clinicos"):
        print("Creando tabla informes_clinicos...")
        with engine.connect() as conn:
            conn.execute(text("""
                CREATE TABLE informes_clinicos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    turno_id INTEGER NOT NULL UNIQUE,
                    paciente_id INTEGER NOT NULL,
                    tipo_informe VARCHAR(50) NOT NULL,
                    contenido_json TEXT NOT NULL,
                    contenido_texto TEXT,
                    estado VARCHAR(50) NOT NULL DEFAULT 'BORRADOR',
                    version INTEGER NOT NULL DEFAULT 1,
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    finalized_at TIMESTAMP,
                    created_by INTEGER NOT NULL,
                    updated_by INTEGER NOT NULL,
                    finalized_by INTEGER,
                    FOREIGN KEY (turno_id) REFERENCES turnos(id) ON DELETE RESTRICT,
                    FOREIGN KEY (paciente_id) REFERENCES pacientes(id),
                    FOREIGN KEY (created_by) REFERENCES users(id),
                    FOREIGN KEY (updated_by) REFERENCES users(id),
                    FOREIGN KEY (finalized_by) REFERENCES users(id)
                )
            """))
            # Create indexes according to index_rules (only on paciente_id and estado)
            conn.execute(text("CREATE INDEX idx_informes_paciente ON informes_clinicos(paciente_id)"))
            conn.execute(text("CREATE INDEX idx_informes_estado ON informes_clinicos(estado)"))
            conn.commit()
        print("Tabla informes_clinicos creada exitosamente.")
    else:
        print("La tabla informes_clinicos ya existe.")

def down():
    inspector = inspect(engine)
    if inspector.has_table("informes_clinicos"):
        print("Eliminando tabla informes_clinicos...")
        with engine.connect() as conn:
            conn.execute(text("DROP TABLE informes_clinicos"))
            conn.commit()
        print("Tabla informes_clinicos eliminada exitosamente.")
    else:
        print("La tabla informes_clinicos no existe.")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--rollback":
        down()
    else:
        up()
