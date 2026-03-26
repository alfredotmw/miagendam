from database import SessionLocal
from models.turno import Turno
from models.agenda import Agenda
from datetime import datetime, timedelta
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def diagnose_radioterapia():
    db = SessionLocal()
    try:
        # Filtros solicitados:
        # - Solo Agenda "Radioterapia Colombia" (ID 4 según init_data.py)
        # - Solo turnos NO cancelados
        # - Solo desde hoy hacia adelante (2026-03-26)
        
        today = datetime(2026, 3, 26, 0, 0, 0)
        
        agenda = db.get(Agenda, 4)
        if not agenda or "COLOMBIA" not in agenda.nombre.upper():
            # Fallback por nombre si el ID 4 no fuera el correcto
            agenda = db.query(Agenda).filter(Agenda.nombre.ilike("%RADIOTERAPIA COLOMBIA%")).first()
            
        if not agenda:
            logger.error("❌ No se encontró la agenda 'RADIOTERAPIA COLOMBIA'")
            return

        slot_minutos = agenda.slot_minutos if agenda.slot_minutos else 10
        logger.info(f"🔍 DIAGNÓSTICO PRODUCCIÓN: {agenda.nombre} (ID: {agenda.id})")
        logger.info(f"   - Slot Configurado: {slot_minutos} min")
        logger.info(f"   - Filtro Fecha: >= {today.date()}")

        # Seleccionar turnos afectados
        turnos_afectados = db.query(Turno).filter(
            Turno.agenda_id == agenda.id,
            Turno.estado != 'CANCELADO',
            Turno.fecha >= today
        ).all()

        total_encontrados = len(turnos_afectados)
        logger.info(f"📊 Total de turnos encontrados en esta agenda (desde hoy): {total_encontrados}")

        logger.info("\n" + "="*80)
        logger.info(f"{'ID':<6} | {'FECHA/HORA':<19} | {'DUR_RAW':<8} | {'SLOTS':<6} | {'¿ACCIÓN?'}")
        logger.info("-" * 80)

        afectados_count = 0
        for t in turnos_afectados:
            duracion_raw = t.duracion
            
            # Lógica de renderización (como en routers/agendas.py)
            t_duracion_calc = t.duracion if t.duracion else 15
            
            num_slots = 0
            t_inicio = t.fecha
            t_fin = t_inicio + timedelta(minutes=t_duracion_calc)
            
            # Simulamos el barrido de slots de la agenda
            # Empezamos en la hora del turno y avanzamos de a slot_minutos
            curr = t_inicio.replace(minute=(t_inicio.minute // slot_minutos) * slot_minutos, second=0, microsecond=0)
            
            while curr < t_fin:
                slot_end = curr + timedelta(minutes=slot_minutos)
                if curr < t_fin and slot_end > t_inicio:
                    num_slots += 1
                curr = slot_end
                if num_slots > 10: break

            if num_slots > 1:
                afectados_count += 1
                accion = "⚠️ NORMALIZAR A 10m"
                logger.info(f"{t.id:<6} | {str(t.fecha):<19} | {str(duracion_raw):<8} | {num_slots:<6} | {accion}")

        logger.info("="*80)
        logger.info(f"📈 RESUMEN: {afectados_count} turnos de {total_encontrados} necesitan normalización.")
        
    except Exception as e:
        logger.error(f"❌ Error durante el diagnóstico: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    diagnose_radioterapia()
