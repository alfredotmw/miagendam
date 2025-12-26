import logging
from database import engine
from sqlalchemy import text, inspect

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def migrate_clinical_p0():
    """
    Agrega columnas para P0 Architecture Upgrade:
    - Estado (Borrador/Firmado)
    - Auditoria (Creado/Editado Por)
    - Firma Digital (Firmado Por)
    """
    inspector = inspect(engine)
    if not inspector.has_table("historia_clinica"):
        logger.error("Tabla 'historia_clinica' no existe. Ejecuta la app para crearla primero.")
        return

    columns = [col["name"] for col in inspector.get_columns("historia_clinica")]
    
    # 1. Estado
    if "estado" not in columns:
        logger.info("Agregando 'estado'...")
        with engine.connect() as conn:
            # Default 'BORRADOR' doesn't backfill correctly in all SQLs if column is recent, but we can try default
            # Or just set a default clause. 
            conn.execute(text("ALTER TABLE historia_clinica ADD COLUMN estado VARCHAR DEFAULT 'BORRADOR'"))
            conn.commit()
    
    # 2. Auditoría (Creado/Editado) - FKs int
    audit_cols = ["creado_por_id", "editado_por_id", "firmado_por_id", "es_enmienda_de_id"]
    for col in audit_cols:
        if col not in columns:
            logger.info(f"Agregando '{col}'...")
            with engine.connect() as conn:
                conn.execute(text(f"ALTER TABLE historia_clinica ADD COLUMN {col} INTEGER"))
                conn.commit()

    # 3. Fechas
    date_cols = ["fecha_creacion", "fecha_edicion", "fecha_firma"]
    for col in date_cols:
        if col not in columns:
            logger.info(f"Agregando '{col}'...")
            with engine.connect() as conn:
                # TIMESTAMP usually works for both PG and SQLite (via SQLAlchemy text)
                # But to be safe in raw SQL:
                dialect = engine.dialect.name
                type_ = "TIMESTAMP" if dialect == "postgresql" else "DATETIME"
                conn.execute(text(f"ALTER TABLE historia_clinica ADD COLUMN {col} {type_}"))
                conn.commit()

    logger.info("Migración P0 completada con éxito.")

if __name__ == "__main__":
    migrate_clinical_p0()
