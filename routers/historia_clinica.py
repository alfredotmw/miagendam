from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models.historia_clinica import HistoriaClinica
from models.turno import Turno
from models.paciente import Paciente
from schemas.historia_clinica import HistoriaClinicaCreate, HistoriaClinicaOut, TimelineResponse, TimelineEvent
from auth.jwt import get_current_user
from typing import List, Optional
from datetime import date, datetime, timedelta
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
def get_timeline(
    paciente_id: int, 
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user) # 🔐 Inject User
):
    # 0. Fetch Paciente
    paciente = db.query(Paciente).filter(Paciente.id == paciente_id).first()
    if not paciente:
        raise HTTPException(status_code=404, detail="Paciente no encontrado")

    # 🛑 PERMISSION CHECK
    # Si el usuario tiene 'allowed_agendas', filtrar lo que ve.
    allowed_ids_str = current_user.get("allowed_agendas")
    allowed_ids = []
    if allowed_ids_str:
        try:
            allowed_ids = [int(x.strip()) for x in allowed_ids_str.split(",") if x.strip()]
        except:
            pass
    
    is_restricted = len(allowed_ids) > 0 and current_user["role"] != "ADMIN"

    # 1. Fetch Notes
    # For now, we show all notes unless strictly needed otherwise. 
    # Notes are context. But if strict needed, we could filter by service match.
    # Leaving notes visible for better context unless user specific request for notes specifically.
    query_notas = db.query(HistoriaClinica).filter(HistoriaClinica.paciente_id == paciente_id)
    if start_date:
        query_notas = query_notas.filter(HistoriaClinica.fecha >= start_date)
    if end_date:
        query_notas = query_notas.filter(HistoriaClinica.fecha <= datetime.combine(end_date, datetime.max.time()))
    
    notas = query_notas.all()
    
    # 2. Fetch Turnos (Strictly Filtered)
    query_turnos = db.query(Turno).filter(Turno.paciente_id == paciente_id)
    
    # 🕵️ APPLY FILTER
    if is_restricted:
        query_turnos = query_turnos.filter(Turno.agenda_id.in_(allowed_ids))

    if start_date:
        query_turnos = query_turnos.filter(Turno.fecha >= start_date)
    if end_date:
        query_turnos = query_turnos.filter(Turno.fecha <= datetime.combine(end_date, datetime.max.time()))

    turnos = query_turnos.all()

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

    # Process Turnos with Grouping Logic
    treatment_events = []
    
    for turno in turnos:
        agenda_nombre = turno.agenda.nombre if turno.agenda else "Agenda desconocida"
        normalized_service = "CONSULTORIO"
        is_treatment = False
        
        # Detect service type
        if "QUIMIO" in agenda_nombre.upper(): 
            normalized_service = "QUIMIOTERAPIA"
            is_treatment = True
        elif "TOMO" in agenda_nombre.upper(): 
            normalized_service = "TOMOGRAFIA"
        elif "RADIO" in agenda_nombre.upper() or "RT" in agenda_nombre.upper(): 
            normalized_service = "RADIOTERAPIA"
            is_treatment = True

        # Group logic
        if is_treatment:
            treatment_events.append({
                "turno": turno,
                "fecha": turno.fecha,
                "servicio": normalized_service,
                "estado": turno.estado,
                "agenda_nombre": agenda_nombre
            })
            continue # Skip adding individual event immediately

        # Add non-treatment events normally
        practica_str = ""
        if turno.practica: practica_str = turno.practica.nombre
        if turno.practicas:
            p_names = [p.nombre for p in turno.practicas]
            if practica_str: p_names.insert(0, practica_str)
            practica_str = ", ".join(p_names)
        
        descripcion = f"Turno: {agenda_nombre}"
        detalle = f"Prácticas: {practica_str if practica_str else 'Consulta/Sin práctica asoc.'}"
        
        timeline_events.append(TimelineEvent(
            tipo="TURNO",
            fecha=turno.fecha, 
            descripcion=descripcion,
            detalle=detalle,
            id_referencia=turno.id,
            servicio=normalized_service,
            estado=turno.estado
        ))

    # Identify and Create Plan Treatment Events
    if treatment_events:
        # Sort by date asc for grouping
        treatment_events.sort(key=lambda x: x["fecha"])
        
        groups = []
        if treatment_events:
            current_group = [treatment_events[0]]
            for i in range(1, len(treatment_events)):
                prev = current_group[-1]
                curr = treatment_events[i]
                
                # Break group if service differs or gap > 60 days
                delta = curr["fecha"] - prev["fecha"]
                if delta.days > 60 or curr["servicio"] != prev["servicio"]:
                    groups.append(current_group)
                    current_group = [curr]
                else:
                    current_group.append(curr)
            groups.append(current_group)

        # Create TimelineEvents for each group
        for group in groups:
            first = group[0]
            last = group[-1]
            count = len(group)
            
            completed = sum(1 for e in group if str(e["estado"]).upper() in ["COMPLETADO", "ASISTIO", "REALIZADO"])
            absent = sum(1 for e in group if str(e["estado"]).upper() in ["AUSENTE", "CANCELADO"])
            pending = count - completed - absent
            
            # Status of the plan
            plan_status = "PENDIENTE"
            if completed > 0: plan_status = "EN_CURSO"
            if completed == count: plan_status = "COMPLETADO"
            
            desc = f"Plan de Tratamiento: {first['servicio']}"
            
            # HTML for detail (will be rendered in frontend)
            det = (f"<strong>Progreso:</strong> {completed}/{count} realizada(s).<br>"
                   f"<small>Inicio: {first['fecha'].strftime('%d/%m/%Y')} - Fin est: {last['fecha'].strftime('%d/%m/%Y')}</small>")

            # Add to timeline (using last date to keep it top-relevant)
            timeline_events.append(TimelineEvent(
                tipo="PLAN_TRATAMIENTO",
                fecha=last["fecha"], 
                descripcion=desc,
                detalle=det,
                id_referencia=first["turno"].id,
                servicio=first["servicio"],
                estado=plan_status
            ))

    # Sort by Date DESC
    timeline_events.sort(key=lambda x: x.fecha, reverse=True)

    return TimelineResponse(
        paciente_id=paciente_id,
        paciente=paciente, # Pydantic will serialize this to PacienteOut
        timeline=timeline_events
    )

@router.get("/dni/{dni}/timeline", response_model=TimelineResponse)
def get_timeline_by_dni(
    dni: str, 
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user) # Pass user
):
    paciente = db.query(Paciente).filter(Paciente.dni == dni).first()
    if not paciente:
        raise HTTPException(status_code=404, detail="Paciente no encontrado")
    
    return get_timeline(paciente.id, start_date, end_date, db, current_user)
