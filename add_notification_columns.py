from sqlalchemy import create_engine, text
import os

# Obtener URL de base de datos
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./agendas.db")
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(DATABASE_URL)

def run_migration():
    with engine.connect() as conn:
        print("🔍 Verificando columnas en tabla 'turnos'...")
        
        # Verificar si es SQLite o Postgres para la sintaxis
        is_sqlite = "sqlite" in DATABASE_URL
        
        try:
            # Intentar agregar columna recordatorio_enviado
            if is_sqlite:
                conn.execute(text("ALTER TABLE turnos ADD COLUMN recordatorio_enviado BOOLEAN DEFAULT 0"))
            else:
                conn.execute(text("ALTER TABLE turnos ADD COLUMN recordatorio_enviado BOOLEAN DEFAULT FALSE"))
            print("✅ Columna 'recordatorio_enviado' agregada.")
        except Exception as e:
            print(f"⚠️  Columna 'recordatorio_enviado' ya existe o error: {e}")

        try:
            conn.execute(text("ALTER TABLE turnos ADD COLUMN recordatorio_fecha DATETIME")) # TIMESTAMP en postgres se mapea a menudo, pero DATETIME suele funcionar
            print("✅ Columna 'recordatorio_fecha' agregada.")
        except Exception as e:
            # En Postgres puede ser TIMESTAMP WITHOUT TIME ZONE
            try:
                if not is_sqlite:
                    conn.execute(text("ALTER TABLE turnos ADD COLUMN recordatorio_fecha TIMESTAMP"))
                    print("✅ Columna 'recordatorio_fecha' agregada (Postgres).")
            except Exception as ex:
                print(f"⚠️  Columna 'recordatorio_fecha' ya existe o error: {ex}")

        try:
            conn.execute(text("ALTER TABLE turnos ADD COLUMN recordatorio_usuario_id INTEGER REFERENCES users(id)"))
            print("✅ Columna 'recordatorio_usuario_id' agregada.")
        except Exception as e:
             # Sintaxis SQLite para FK es más compleja en alter table, a veces solo se agrega el entero
            try:
                conn.execute(text("ALTER TABLE turnos ADD COLUMN recordatorio_usuario_id INTEGER"))
                print("✅ Columna 'recordatorio_usuario_id' agregada (Simple Int).")
            except Exception as ex:
                print(f"⚠️  Columna 'recordatorio_usuario_id' ya existe o error: {ex}")

        print("🚀 Migración finalizada.")

if __name__ == "__main__":
    run_migration()
