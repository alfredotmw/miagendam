from fastapi import APIRouter, Depends, Query, HTTPException, Response
from sqlalchemy.orm import Session
from database import get_db
from models.turno import Turno
from models.paciente import Paciente
from models.agenda import Agenda
from datetime import date
import csv
import io

router = APIRouter(prefix="/exports", tags=["Exports"])


@router.get("/turnos")
def export_turnos(
    desde: date = Query(..., description="Fecha desde (YYYY-MM-DD)"),
    hasta: date = Query(..., description="Fecha hasta (YYYY-MM-DD)"),
    formato: str = Query("json", description="Formato de salida: json o csv"),
    db: Session = Depends(get_db)
):
    """
    Exporta turnos entre fechas dadas.
    Permite formato JSON (por defecto) o CSV.
    """

    turnos = (
        db.query(Turno)
        .join(Paciente, Paciente.dni == Turno.dni)
        .join(Agenda, Agenda.id == Turno.agenda_id)
        .filter(Turno.fecha.between(desde, hasta))
        .all()
    )

    if not turnos:
        raise HTTPException(status_code=404, detail="No hay turnos en el rango indicado")

    # 🧩 Transformar datos a lista de diccionarios
    data = []
    for t in turnos:
        data.append({
            "dni": t.dni,
            "paciente": t.paciente.apellido_nombre if t.paciente else None,
            "fecha": t.fecha.isoformat(),
            "hora": str(t.hora),
            "duracion_minutos": t.duracion_minutos,
            "realizado": t.realizado,
            "agenda": t.agenda.nombre if t.agenda else None,
            "tipo_agenda": t.agenda.tipo if t.agenda else None
        })

    # 📤 Exportar como JSON
    if formato.lower() == "json":
        return data

    # 📤 Exportar como CSV
    elif formato.lower() == "csv":
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)

        return Response(
            content=output.getvalue(),
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename=turnos_{desde}_{hasta}.csv"
            },
        )

    else:
        raise HTTPException(status_code=400, detail="Formato inválido. Use 'json' o 'csv'.")
