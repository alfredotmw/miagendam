import sys
import os
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker

# Add current dir to path
sys.path.append(os.getcwd())

from database import engine

def migrate():
    print("🔍 Iniciando migración de campos para Nueva Evolución...")
    
    # 1. Definir los nuevos campos y sus tipos para Postgres/SQLite
    # Usamos TEXT para JSON en SQLite (fallback) si es necesario, pero SQLAlchemy JSON lo maneja
    new_columns = [
        ("examen_fisico_estructurado", "JSON"),
        ("indicaciones", "JSON"),
        ("proximo_control", "DATE"),
        ("pautas_alarma", "TEXT"),
        ("situacion_cierre", "VARCHAR")
    ]
    
    inspector = inspect(engine)
    columns_in_db = [c['name'] for c in inspector.get_columns("historia_clinica")]
    
    with engine.begin() as conn:
        for col_name, col_type in new_columns:
            if col_name not in columns_in_db:
                print(f"🚀 Agregando columna: {col_name} ({col_type})...")
                try:
                    conn.execute(text(f"ALTER TABLE historia_clinica ADD COLUMN {col_name} {col_type}"))
                    print(f"✅ Columna {col_name} agregada con éxito.")
                except Exception as e:
                    print(f"❌ Error al agregar {col_name}: {e}")
            else:
                print(f"✨ La columna {col_name} ya existe. Saltando...")

    print("🎉 Proceso de migración finalizado.")

if __name__ == "__main__":
    migrate()
