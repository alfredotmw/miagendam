
import logging
from sqlalchemy import text
from database import SessionLocal, engine
from models.user import User
from models.agenda import Agenda

# Configuración de logging profesional
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def migrate_legacy_permissions(db):
    """
    Migra los permisos de agendas desde la columna CSV (allowed_agendas) 
    a la relación muchos-a-muchos (user_agendas).
    Es seguro ejecutarlo varias veces ya que solo agrega las faltantes.
    """
    try:
        users = db.query(User).all()
        all_agendas = db.query(Agenda).all()
        agenda_map = {a.id: a for a in all_agendas}
        
        logger.info(f"Verificando migración de permisos para {len(users)} usuarios...")
        
        for u in users:
            if not u.allowed_agendas:
                continue
            
            try:
                # Extrae los IDs de la columna CSV
                legacy_ids = [int(id_str.strip()) for id_str in u.allowed_agendas.split(',') if id_str.strip()]
                current_m2m_ids = {a.id for a in u.agendas}
                
                added_count = 0
                for aid in legacy_ids:
                    if aid in agenda_map and aid not in current_m2m_ids:
                        u.agendas.append(agenda_map[aid])
                        added_count += 1
                
                if added_count > 0:
                    logger.info(f"Usuario {u.username}: Se migraron {added_count} permisos de agenda.")
            except Exception as e:
                logger.warning(f"Error procesando permisos para usuario {u.username}: {e}")
        
        db.commit()
    except Exception as e:
        logger.error(f"Falla crítica en migración de permisos: {e}")
        db.rollback()

def ensure_audit_columns():
    """
    Asegura que las columnas de auditoría existan en las tablas principales.
    Utiliza IF NOT EXISTS para compatibilidad con PostgreSQL y manejo de errores para SQLite.
    """
    tables_full = ["turnos", "pacientes", "obras_sociales", "medicos_derivantes"]
    tables_partial = ["seguimiento_radioterapia"]
    
    with engine.connect() as conn:
        # Tablas con auditoría completa (creación y modificación)
        for table in tables_full:
            columns = [
                ("creado_por_id", "INTEGER"),
                ("fecha_creacion", "TIMESTAMP DEFAULT NOW()"),
                ("modificado_por_id", "INTEGER"),
                ("fecha_modificacion", "TIMESTAMP")
            ]
            for col_name, col_type in columns:
                try:
                    query = text(f"ALTER TABLE {table} ADD COLUMN {col_name} {col_type}")
                    conn.execute(query)
                    conn.commit()
                    logger.info(f"Tabla {table}: Columna '{col_name}' creada.")
                except Exception:
                    # Silenciamos el error si ya existe (común en despliegues repetidos)
                    pass

        # Tablas con auditoría parcial (solo IDs de usuario)
        for table in tables_partial:
            columns = [
                ("creado_por_id", "INTEGER"),
                ("modificado_por_id", "INTEGER")
            ]
            for col_name, col_type in columns:
                try:
                    query = text(f"ALTER TABLE {table} ADD COLUMN {col_name} {col_type}")
                    conn.execute(query)
                    conn.commit()
                    logger.info(f"Tabla {table} (parcial): Columna '{col_name}' creada.")
                except Exception:
                    pass

def main():
    logger.info("--- Iniciando Saneamiento de Base de Datos ---")
    
    # 1. Asegurar esquema de auditoría
    ensure_audit_columns()
    
    # 2. Sincronizar permisos M2M
    db = SessionLocal()
    try:
        migrate_legacy_permissions(db)
        logger.info("--- Proceso completado exitosamente ---")
    finally:
        db.close()

if __name__ == "__main__":
    main()
