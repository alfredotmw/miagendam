from database import SessionLocal
from models.turno import Turno
from datetime import datetime
from sqlalchemy import text
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def execute_fix():
    db = SessionLocal()
    try:
        # Criterios exactos aprobados
        agenda_id = 4 # Radioterapia Colombia
        today_str = "2026-03-26"
        
        # 1. PASO: Conteo previo (Dry-Run logic)
        query_count = text("""
            SELECT COUNT(*) 
            FROM turnos 
            WHERE agenda_id = :aid 
              AND estado != 'CANCELADO' 
              AND fecha >= :today 
              AND (duracion IS NULL OR duracion > 10)
        """)
        
        count = db.execute(query_count, {"aid": agenda_id, "today": today_str}).scalar()
        logger.info(f"📊 REGISTROS A MODIFICAR: {count}")
        
        if count == 0:
            logger.info("✅ No hay registros que necesiten actualización según los criterios.")
            return

        # 2. PASO: Confirmación y UPDATE
        # Nota: Como es un script de un solo paso, procedemos al update directamente
        # pero informando qué se está haciendo.
        
        logger.info(f"🚀 Ejecutando UPDATE para normalizar a 10 min...")
        
        query_update = text("""
            UPDATE turnos 
            SET duracion = 10 
            WHERE agenda_id = :aid 
              AND estado != 'CANCELADO' 
              AND fecha >= :today 
              AND (duracion IS NULL OR duracion > 10)
        """)
        
        result = db.execute(query_update, {"aid": agenda_id, "today": today_str})
        db.commit()
        
        logger.info(f"✅ ÉXITO: Se actualizaron {result.rowcount} registros.")
        logger.info("ℹ️ Ahora los turnos deberían ocupar un solo slot de 10 minutos y el borrado visual será consistente.")

    except Exception as e:
        logger.error(f"❌ Error durante la ejecución: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    execute_fix()
