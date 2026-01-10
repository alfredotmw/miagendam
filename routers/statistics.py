from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from database import get_db
from models.turno import Turno
from models.paciente import Paciente
from models.agenda import Agenda
from models.medico import MedicoDerivante
from auth.jwt import SECRET_KEY, ALGORITHM
from jose import jwt, JWTError

router = APIRouter(
    prefix="/estadisticas",
    tags=["Estadisticas"]
)

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
