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
        .join(Paciente, Paciente.id == Turno.paciente_id)
        .join(Agenda, Agenda.id == Turno.agenda_id)
        .filter(Turno.fecha >= desde, Turno.fecha <= hasta) # Usar comparación directa o between
        .all()
    )

    if not turnos:
        raise HTTPException(status_code=404, detail="No hay turnos en el rango indicado")

    # 🧩 Transformar datos a lista de diccionarios
    data = []
    for t in turnos:
        paciente_nombre = f"{t.paciente.apellido}, {t.paciente.nombre}" if t.paciente else "Desconocido"
        
        # Priorizar celular, sino telefono
        contacto = t.paciente.celular if t.paciente and t.paciente.celular else (t.paciente.telefono if t.paciente else "")

        data.append({
            "Fecha": t.fecha.strftime("%Y-%m-%d"),
            "Hora": t.hora,
            "Paciente": paciente_nombre,
            "DNI": t.paciente.dni if t.paciente else "",
            "Celular": contacto, # Columna solicitada
            "Agenda": t.agenda.nombre if t.agenda else "",
            "Tipo": t.agenda.tipo if t.agenda else "",
            "Estado": t.estado,
            "Duracion": t.duracion,
            "Practicas": ", ".join([p.nombre for p in t.practicas]) if t.practicas else ""
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
