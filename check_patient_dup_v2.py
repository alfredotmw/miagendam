from database import SessionLocal
from models.turno import Turno
from models.paciente import Paciente
from models.agenda import Agenda
from sqlalchemy import extract, or_

def check_patient_turnos_v2():
    db = SessionLocal()
    try:
        # Buscar pacientes de forma más laxa
        # Apelllido contiene Nu y termina en ez/ez
        pacientes = db.query(Paciente).filter(
            or_(
                Paciente.apellido.ilike("%Nuñez%"),
                Paciente.apellido.ilike("%Nunez%"),
                 Paciente.apellido.ilike("%Nu?ez%")
            )
        ).all()
        
        print(f"Encontrados {len(pacientes)} pacientes con apellido similar a Nuñez:")
        
        target_paciente = None
        for p in pacientes:
            print(f" - {p.apellido}, {p.nombre} (ID: {p.id}) DOB: {p.fecha_nacimiento}")
            if "Mirta" in p.nombre or "Elena" in p.nombre:
                target_paciente = p

        if not target_paciente:
             print("No se encontró ninguna Mirta o Elena Nuñez. Buscando per Agenda y Fecha...")
             # Fallback: buscar por fecha y agenda directamente
             # 29/01/2026 10:45
             turnos_fecha = db.query(Turno).filter(
                extract('year', Turno.fecha) == 2026,
                extract('month', Turno.fecha) == 1,
                extract('day', Turno.fecha) == 29
             ).all()
             
             for t in turnos_fecha:
                 if t.hora == "10:45":
                     print(f"  FOUND BY DATE/TIME: Turno ID {t.id} - Paciente: {t.paciente.apellido}, {t.paciente.nombre}", f"Agenda: {t.agenda.nombre}")
                     target_paciente = t.paciente
        
        if target_paciente:
            print(f"\nAnalizando paciente seleccionado: {target_paciente.apellido}, {target_paciente.nombre} (ID: {target_paciente.id})")
            turnos = db.query(Turno).filter(
                Turno.paciente_id == target_paciente.id,
                extract('year', Turno.fecha) == 2026,
                extract('month', Turno.fecha) == 1,
                extract('day', Turno.fecha) == 29
            ).all()

            for t in turnos:
                print(f"  Turno ID: {t.id}")
                print(f"    Fecha: {t.fecha}")
                print(f"    Hora: {t.hora}")
                print(f"    Agenda: {t.agenda.nombre if t.agenda else 'N/A'}")
                print(f"    Prácticas asociadas (Relation 'practicas' - Tabla intermedia):")
                if t.practicas:
                    for prac in t.practicas:
                        print(f"      - {prac.nombre} (ID: {prac.id})")
                else:
                    print("      Ninguna (Lista vacía)")
                    
                print(f"    Práctica única legacy (Relation 'practica' - FK directa): {t.practica.nombre if t.practica else 'Ninguna'}")

    finally:
        db.close()

if __name__ == "__main__":
    check_patient_turnos_v2()
