from database import SessionLocal
from models.turno import Turno
from models.agenda import Agenda
from sqlalchemy import func, text

def detect_duplicate_turnos():
    db = SessionLocal()
    try:
        print("🔍 Buscando turnos duplicados (Misma Agenda + Fecha + Hora)...")
        
        # Agrupar por Agenda, Fecha, Hora y contar
        # Excluyendo cancelados
        query = db.query(
            Turno.agenda_id,
            Turno.fecha, # This is datetime
            Turno.hora,
            func.count(Turno.id).label('count')
        ).filter(
            Turno.estado != 'CANCELADO'
        ).group_by(
            Turno.agenda_id,
            Turno.fecha,
            Turno.hora
        ).having(
            func.count(Turno.id) > 1
        )
        
        duplicates = query.all()
        
        if not duplicates:
            print("✅ No se encontraron turnos duplicados.")
            return

        print(f"⚠️ Se encontraron {len(duplicates)} horarios con duplicados:\n")
        
        for dup in duplicates:
            agenda_id = dup.agenda_id
            fecha = dup.fecha
            hora = dup.hora
            count = dup.count
            
            agenda = db.get(Agenda, agenda_id)
            agenda_nombre = agenda.nombre if agenda else "Desconocida"
            
            print(f"📍 Agenda: {agenda_nombre} (ID: {agenda_id}) | Fecha: {fecha} | Hora: {hora} | Cantidad: {count}")
            
            # Detalle de los turnos
            turnos_detalle = db.query(Turno).filter(
                Turno.agenda_id == agenda_id,
                Turno.fecha == fecha,
                Turno.hora == hora,
                Turno.estado != 'CANCELADO'
            ).all()
            
            for t in turnos_detalle:
                paciente_nombre = f"{t.paciente.nombre} {t.paciente.apellido}" if t.paciente else "Sin Paciente"
                print(f"   - ID: {t.id} | Paciente: {paciente_nombre} (ID: {t.paciente_id}) | Estado: {t.estado}")
            
            print("-" * 50)

    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    detect_duplicate_turnos()
