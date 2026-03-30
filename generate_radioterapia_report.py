from database import SessionLocal
from models.turno import Turno
from datetime import datetime, timedelta
import csv

def generate_report():
    db = SessionLocal()
    try:
        agenda_id = 4
        today = datetime(2026, 3, 26, 0, 0, 0)
        slot_minutos = 10
        
        turnos = db.query(Turno).filter(
            Turno.agenda_id == agenda_id,
            Turno.estado != 'CANCELADO',
            Turno.fecha >= today
        ).all()

        affected = []
        for t in turnos:
            t_dur = t.duracion if t.duracion else 15
            t_inicio = t.fecha
            t_fin = t_inicio + timedelta(minutes=t_dur)
            
            # Contar slots
            num_slots = 0
            curr = t_inicio.replace(minute=(t_inicio.minute // slot_minutos) * slot_minutos, second=0, microsecond=0)
            while curr < t_fin:
                slot_end = curr + timedelta(minutes=slot_minutos)
                if curr < t_fin and slot_end > t_inicio:
                    num_slots += 1
                curr = slot_end
                
            if num_slots > 1:
                # Calcular alineación sugerida (múltiplo de 10 más cercano)
                remainder = t_inicio.minute % slot_minutos
                if remainder <= 5:
                    new_min = t_inicio.minute - remainder
                else:
                    new_min = t_inicio.minute + (slot_minutos - remainder)
                
                new_time = t_inicio.replace(minute=0, second=0, microsecond=0) + timedelta(minutes=((t_inicio.hour * 60) + new_min))
                
                affected.append({
                    "id": t.id,
                    "actual": t_inicio.strftime("%Y-%m-%d %H:%M"),
                    "duracion": t_dur,
                    "slots": num_slots,
                    "sugerido": new_time.strftime("%H:%M")
                })
        
        # Guardar a CSV para que el asistente lo lea
        with open("/tmp/radioterapia_report.csv", "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["id", "actual", "duracion", "slots", "sugerido"])
            writer.writeheader()
            writer.writerows(affected)
            
        print(f"Reporte generado con {len(affected)} registros.")

    finally:
        db.close()

if __name__ == "__main__":
    generate_report()
