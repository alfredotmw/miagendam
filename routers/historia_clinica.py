from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models.historia_clinica import HistoriaClinica
from models.turno import Turno
from models.paciente import Paciente
from schemas.historia_clinica import HistoriaClinicaCreate, HistoriaClinicaOut, TimelineResponse, TimelineEvent
from auth.jwt import get_current_user
from typing import List
from sqlalchemy import desc

router = APIRouter(
    prefix="/historia-clinica",
    tags=["Historia Clinica"]
)

@router.post("/", response_model=HistoriaClinicaOut)
def crear_nota(
    nota: HistoriaClinicaCreate, 
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    # Verify patient exists
    paciente = db.query(Paciente).filter(Paciente.id == nota.paciente_id).first()
    if not paciente:
        raise HTTPException(status_code=404, detail="Paciente no encontrado")

    nueva_nota = HistoriaClinica(
        paciente_id=nota.paciente_id,
        texto=nota.texto,
        servicio=nota.servicio,
        medico_id=current_user.get("id") # Asignar usuario logueado si existe
    )
    db.add(nueva_nota)
    db.commit()
    db.refresh(nueva_nota)
    return nueva_nota

@router.get("/paciente/{paciente_id}/timeline", response_model=TimelineResponse)
def get_timeline(paciente_id: int, db: Session = Depends(get_db)):
    # 1. Fetch Notes
    notas = db.query(HistoriaClinica).filter(HistoriaClinica.paciente_id == paciente_id).all()
    
    # 2. Fetch Turnos (Past and Future or just all? User implied history so maybe all, but sorted)
    # Including 'Agenda' and 'Practicas' to be useful
    turnos = db.query(Turno).filter(Turno.paciente_id == paciente_id).all()

    timeline_events = []

    # Process Notes
    for nota in notas:
        timeline_events.append(TimelineEvent(
            tipo="NOTA",
            fecha=nota.fecha,
            descripcion=f"Nota de {nota.servicio}",
            detalle=nota.texto,
            id_referencia=nota.id,
            servicio=nota.servicio,
            estado="Guardado"
        ))

    # Process Turnos
    for turno in turnos:
        # Determine Description (Service/Agenda + Practice)
        agenda_nombre = turno.agenda.nombre if turno.agenda else "Agenda desconocida"
        practica_str = ""
        
        # Check single practice
        if turno.practica:
            practica_str = turno.practica.nombre
        
        # Check multipractice
        if turno.practicas:
            p_names = [p.nombre for p in turno.practicas]
            if practica_str:
                p_names.insert(0, practica_str)
            practica_str = ", ".join(p_names)
        
        descripcion = f"Turno: {agenda_nombre}"
        detalle = f"Prácticas: {practica_str if practica_str else 'Consulta/Sin práctica asoc.'}"

        timeline_events.append(TimelineEvent(
            tipo="TURNO",
            fecha=turno.fecha, # This is a date usually, need to combine with hora if possible or just use date
            descripcion=descripcion,
            detalle=detalle,
            id_referencia=turno.id,
            servicio=agenda_nombre,
            estado=turno.estado
        ))
    
    # Sort by Date DESC
    timeline_events.sort(key=lambda x: x.fecha, reverse=True)

    return TimelineResponse(paciente_id=paciente_id, timeline=timeline_events)

@router.get("/dni/{dni}/timeline", response_model=TimelineResponse)
def get_timeline_by_dni(dni: str, db: Session = Depends(get_db)):
    paciente = db.query(Paciente).filter(Paciente.dni == dni).first()
    if not paciente:
        # Return empty timeline if patient not found, or error? 
        # Better 404
        raise HTTPException(status_code=404, detail="Paciente no encontrado")
    
    return get_timeline(paciente.id, db)
