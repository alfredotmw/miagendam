
import logging
from sqlalchemy import text, create_engine
from sqlalchemy.orm import Session
from database import SessionLocal, SQLALCHEMY_DATABASE_URL, engine
from models.user import User
from models.agenda import Agenda
import os

# Configuración de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def migrate_permissions(db: Session):
    """Migra permisos de legacy CSV a M2M relationship."""
    try:
        users = db.query(User).all()
        all_agendas = db.query(Agenda).all()
        agenda_map = {a.id: a for a in all_agendas}
        
        logger.info(f"Iniciando migración de permisos para {len(users)} usuarios...")
        
        for u in users:
            if not u.allowed_agendas:
                continue
            
            try:
                legacy_ids = [int(id_str.strip()) for id_str in u.allowed_agendas.split(',') if id_str.strip()]
                current_m2m_ids = {a.id for a in u.agendas}
                
                added_count = 0
                for aid in legacy_ids:
                    if aid in agenda_map and aid not in current_m2m_ids:
                        u.agendas.append(agenda_map[aid])
                        added_count += 1
                
                if added_count > 0:
                    logger.info(f"User {u.username}: Agregadas {added_count} agendas a la relación M2M.")
            except Exception as e:
                logger.error(f"Error procesando permisos de {u.username}: {e}")
        
        db.commit()
    except Exception as e:
        logger.error(f"Error en migrate_permissions: {e}")
        db.rollback()

def add_audit_columns():
    """Agrega columnas de auditoría de forma segura (PostgreSQL/SQLite)."""
    tables_to_full_audit = ["turnos", "pacientes", "obras_sociales", "medicos_derivantes"]
    tables_to_partial_audit = ["seguimiento_radioterapia"]
    
    with engine.connect() as conn:
        # Full Audit Tables
        for table in tables_to_full_audit:
            logger.info(f"Verificando auditoría para tabla: {table}")
            columns = [
                ("creado_por_id", "INTEGER"),
                ("fecha_creacion", "TIMESTAMP"),
                ("modificado_por_id", "INTEGER"),
                ("fecha_modificacion", "TIMESTAMP")
            ]
            for col_name, col_type in columns:
                try:
                    # Intentar agregar columna. SQL estándar compatible con Postgres y SQLite.
                    conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {col_name} {col_type}"))
                    conn.commit()
                    logger.info(f"  - Columna {col_name} agregada a {table}.")
                except Exception:
                    # Si falla es porque probablemente ya existe.
                    # conn.rollback() # No necesario en todos los dialectos post-error pero buena práctica
                    pass

        # Partial Audit Tables
        for table in tables_to_partial_audit:
            logger.info(f"Verificando auditoría parcial para tabla: {table}")
            columns = [
                ("creado_por_id", "INTEGER"),
                ("modificado_por_id", "INTEGER")
            ]
            for col_name, col_type in columns:
                try:
                    conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {col_name} {col_type}"))
                    conn.commit()
                    logger.info(f"  - Columna {col_name} agregada a {table}.")
                except Exception:
                    pass

def main():
    logger.info("🚀 Iniciando Proceso de Migración en Producción...")
    
    # 1. Agregar Columnas (Esquema)
    add_audit_columns()
    
    # 2. Migrar Datos (Permisos)
    db = SessionLocal()
    try:
        migrate_permissions(db)
        logger.info("✅ Proceso de migración finalizado exitosamente.")
    finally:
        db.close()

if __name__ == "__main__":
    main()
