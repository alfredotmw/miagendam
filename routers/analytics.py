from fastapi import APIRouter, Depends, HTTPException, Query
from auth.jwt import SECRET_KEY, ALGORITHM
from jose import jwt, JWTError
from models.medico import MedicoDerivante
from sqlalchemy.orm import Session
from database import get_db
from models.turno import Turno
from models.paciente import Paciente
from models.agenda import Agenda
from models.practica import Practica
from models.medico import MedicoDerivante
from models.turno_practica import TurnoPractica
import pandas as pd
from datetime import date

router = APIRouter(
    prefix="/analytics",
    tags=["Analytics"],
)

@router.get("/live_data")
def get_live_data(db: Session = Depends(get_db)):
    """
    Retorna un JSON plano optimizado para Excel Power Query (Datos -> Desde Web).
    Formato solicitado:
    1. Fecha (dd/mm/yyyy)
    2. Hora (hh:mm:ss)
    3. DNI
    4. Paciente
    5. Obra Social
    6. Sexo
    7. Edad
    8. Estudio Solicitado (una fila por práctica)
    9. Servicio
    10. Estado
    """
    # Query con Joins para obtener una fila por práctica (Explode)
    results = db.query(Turno, Practica).join(TurnoPractica, Turno.id == TurnoPractica.turno_id).join(Practica, TurnoPractica.practica_id == Practica.id).all()
    
    data = []
    for turno, practica in results:
        # Calcular edad
        edad = None
        if turno.paciente.fecha_nacimiento:
            hoy = date.today()
            fn = turno.paciente.fecha_nacimiento
            edad = hoy.year - fn.year - ((hoy.month, hoy.day) < (fn.month, fn.day))

        # Formatear Hora (hh:mm:ss)
        hora_fmt = turno.hora
        if len(hora_fmt) == 5: # "09:00" -> "09:00:00"
            hora_fmt += ":00"

        row = {
            "Fecha": turno.fecha.strftime("%d/%m/%Y"),
            "Hora": hora_fmt,
            "DNI": turno.paciente.dni,
            "Paciente": f"{turno.paciente.apellido}, {turno.paciente.nombre}",
            "Celular": turno.paciente.celular if (turno.paciente and turno.paciente.celular) else (turno.paciente.telefono if (turno.paciente and turno.paciente.telefono) else "N/A"),
            "Obra Social": turno.paciente.obra_social.nombre if turno.paciente.obra_social else "N/A",
            "Sexo": turno.paciente.sexo,
            "Edad": edad,
            "Estudio Solicitado": practica.nombre,
            "Servicio": turno.agenda.nombre,
            "Médico Solicitante": turno.medico_derivante.nombre if turno.medico_derivante else "N/A",
            "Estado": turno.estado
        }
        data.append(row)

    return data

@router.get("/download")
def download_excel(db: Session = Depends(get_db)):
    """
    Genera y descarga un archivo Excel con los datos actuales.
    """
    # Reutilizamos la lógica de live_data para obtener los datos
    data = get_live_data(db)
    
    # Crear DataFrame
    df = pd.DataFrame(data)
    
    # Guardar en un archivo temporal (o en memoria)
    file_path = "reporte_agendas.xlsx"
    df.to_excel(file_path, index=False)
    
    from fastapi.responses import FileResponse
    return FileResponse(path=file_path, filename="Reporte_Agendas_Medicas.xlsx", media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

@router.get("/excel_feed")
def get_excel_feed(
    token: str = Query(..., description="JWT Token for authentication"),
    db: Session = Depends(get_db)
):
    # Verify Token manually (query param auth for Excel)
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if "sub" not in payload:
            raise HTTPException(status_code=401, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    # Query all turns
    # We join with relevant tables to optimize fetching
    turnos = db.query(Turno).join(Paciente).join(Agenda).outerjoin(MedicoDerivante).order_by(Turno.fecha.desc()).all()
    
    data = []
    for t in turnos:
        # Calculate Age
        edad = t.paciente.edad
        
        # Format Date and Time
        fecha_str = t.fecha.strftime("%Y-%m-%d") if t.fecha else ""
        hora_str = t.hora
        
        # Determine Status
        estado = t.estado
        
        # Determine Referral
        derivante = t.medico_derivante.nombre if t.medico_derivante else ""
        
        # Build Record
        record = {
            "ID_Turno": t.id,
            "Fecha": fecha_str,
            "Hora": hora_str,
            "Semana": t.fecha.isocalendar()[1] if t.fecha else "",
            "Mes": t.fecha.month if t.fecha else "",
            "Año": t.fecha.year if t.fecha else "",
            "Paciente": f"{t.paciente.apellido}, {t.paciente.nombre}",
            "DNI": t.paciente.dni,
            "Edad": edad,
            "Obra_Social": t.paciente.obra_social.nombre if t.paciente.obra_social else "",
            "Agenda_Servicio": t.agenda.nombre,
            "Estado": estado,
            "Medico_Derivante": derivante,
            "Patologia": t.patologia or "",
            # Include Practices?
            "Practicas": ", ".join([p.nombre for p in t.practicas]) if t.practicas else ""
        }
        data.append(record)
        
    return data
