from database import SessionLocal
from models.radioterapia import SeguimientoRadioterapia
from routers.radioterapia import get_excel_feed, check_and_autofill
from datetime import date
import json

# Mock DB Session
db = SessionLocal()

try:
    print("Querying registros...")
    registros = db.query(SeguimientoRadioterapia).order_by(SeguimientoRadioterapia.id.desc()).all()
    print(f"Found {len(registros)} registros.")

    print("Running autofill logic...")
    for reg in registros:
        try:
            check_and_autofill(reg, db)
        except Exception as e:
            print(f"Error in autofill for reg {reg.id}: {e}")

    print("Building JSON data...")
    data = []
    for reg in registros:
        try:
            pat = reg.paciente
            item = {
                "ID": reg.id,
                "Fecha": str(reg.fecha_consulta) if reg.fecha_consulta else None,
                "Apellido": pat.apellido if pat else "",
                "Nombre": pat.nombre if pat else "",
                "DNI": pat.dni if pat else "",
                "Patologia": reg.patologia,
                "Dosis": reg.dosis_total,
                "Fracciones": reg.numero_fracciones,
                "Medico_Responsable": reg.medico_responsable,
                "Medico_Derivante": reg.medico_derivante,
                "Fecha_TAC": str(reg.fecha_tac) if reg.fecha_tac else None,
                "Inicio_Tto": str(reg.fecha_inicio) if reg.fecha_inicio else None,
                "Fin_Tto": str(reg.fecha_fin) if reg.fecha_fin else None,
                "Estado": ("Finalizado" if reg.fecha_fin and reg.fecha_fin < date.today() else "En Curso") if reg.fecha_inicio else "Pendiente",
                "Observaciones": reg.observaciones
            }
            data.append(item)
        except Exception as e:
             print(f"Error building item for reg {reg.id}: {e}")
             raise e

    print("Serialization check...")
    json_output = json.dumps(data)
    print("Success! JSON length:", len(json_output))

except Exception as e:
    print("\nCRITICAL ERROR REPRODUCED:")
    print(e)
finally:
    db.close()
