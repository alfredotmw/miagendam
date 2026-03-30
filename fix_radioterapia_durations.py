from database import SessionLocal, engine
from models.turno import Turno
from models.agenda import Agenda
from sqlalchemy import text
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fix_durations():
    db = SessionLocal()
    try:
        # 1. Identificar la agenda de Radioterapia Colombia
        agenda = db.query(Agenda).filter(Agenda.nombre.ilike("%RADIOTERAPIA COLOMBIA%")).first()
        if not agenda:
            logger.error("❌ No se encontró la agenda 'RADIOTERAPIA COLOMBIA'")
            return

        logger.info(f"✅ Agenda encontrada: {agenda.nombre} (ID: {agenda.id})")

        # 2. Buscar turnos con duración ≠ 10 en esa agenda (solo futuros o recientes para no afectar histórico innecesariamente, o todos)
        # Vamos a corregir todos los turnos 'pendientes' o futuros para limpiar la vista.
        turnos = db.query(Turno).filter(
            Turno.agenda_id == agenda.id,
            Turno.duracion != 10,
            Turno.estado != 'CANCELADO'
        ).all()

        if not turnos:
            logger.info("✨ No hay turnos con duración incorrecta en esta agenda.")
            return

        logger.info(f"🔍 Encontrados {len(turnos)} turnos para corregir.")

        for t in turnos:
            logger.info(f"   - Corrigiendo Turno ID: {t.id} | Hora: {t.hora} | Duración antigua: {t.duracion} -> Nueva: 10")
            t.duracion = 10
        
        db.commit()
        logger.info("🚀 Corrección completada exitosamente.")

    except Exception as e:
        logger.error(f"❌ Error durante la corrección: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    fix_durations()
