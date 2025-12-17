import logging
from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine

logger = logging.getLogger(__name__)

def check_and_migrate_db(engine: Engine):
    """
    Verifica si faltan columnas en la base de datos y las agrega.
    Esto es una migración simple 'manual' para evitar usar Alembic por ahora.
    """
    inspector = inspect(engine)
    
    # 1. Verificar tabla 'turnos'
    if inspector.has_table("turnos"):
        columns = [col["name"] for col in inspector.get_columns("turnos")]
        
        # Chequear columna 'patologia'
        if "patologia" not in columns:
            logger.info("⚠️ Columna 'patologia' faltante en 'turnos'. Agregando...")
            with engine.connect() as conn:
                conn.execute(text("ALTER TABLE turnos ADD COLUMN patologia VARCHAR"))
                conn.commit()
            logger.info("✅ Columna 'patologia' agregada exitosamente.")
        else:
            logger.info("✅ Columna 'patologia' ya existe en 'turnos'.")

        # Chequear columna 'duracion' (por si acaso falto en deploy anteriores)
        if "duracion" not in columns:
            logger.info("⚠️ Columna 'duracion' faltante en 'turnos'. Agregando...")
            with engine.connect() as conn:
                conn.execute(text("ALTER TABLE turnos ADD COLUMN duracion INTEGER"))
                conn.commit()
            logger.info("✅ Columna 'duracion' agregada exitosamente.")
