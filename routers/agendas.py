from datetime import date, datetime, timedelta, time
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from database import get_db
from models.agenda import Agenda
from models.turno import Turno
from models.practica import Practica
from auth.jwt import get_current_user
from services.turno_service import calculate_duration

router = APIRouter(prefix="/agendas", tags=["Agendas"])

@router.get("/")
def listar_agendas(db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    query = db.query(Agenda)
    
    # 🛡️ Service Selector Logic
    
    # 1. Check for Explicitly Allowed Agendas (Priority)
    allowed_ids_str = current_user.get("allowed_agendas")
    if allowed_ids_str:
        # "1,2,5" -> [1, 2, 5]
        try:
            allowed_ids = [int(x.strip()) for x in allowed_ids_str.split(",") if x.strip()]
            if allowed_ids:
                query = query.filter(Agenda.id.in_(allowed_ids))
                return query.all()
        except ValueError:
            pass # Malformed string, ignore and fallback

    # 2. Check for Role-Based Filtering (Fallback)
    if current_user["role"] == "MEDICO":
        # Flexible Name Matching
        search_term = f"%{current_user['username']}%"
        query = query.filter(Agenda.profesional.ilike(search_term))
        
    agendas = query.all()
    return agendas

@router.get("/{agenda_id}/slots")
def get_agenda_slots(
    agenda_id: int,
    fecha: date,
    practica_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    agenda = db.get(Agenda, agenda_id)
    if not agenda:
        raise HTTPException(status_code=404, detail="Agenda no encontrada")

    # Determinar duración del slot y capacidad
    duracion_slot = 20 # Default
    capacity = 1 # Default capacity (simultaneous slots)

    if practica_id:
        practica = db.get(Practica, practica_id)
        if practica:
            # Simulamos una lista de prácticas para la función de servicio
            duracion_slot = calculate_duration(agenda.tipo, [practica])
    else:
        # Si no hay práctica seleccionada, usamos un default según el tipo de agenda
        if agenda.tipo == "ECOGRAFIA": duracion_slot = 30
        elif agenda.tipo == "TOMOGRAFIA": duracion_slot = 20
        elif agenda.tipo == "RESONANCIA": duracion_slot = 30
        elif agenda.tipo == "CONSULTA_MEDICA": duracion_slot = 20
        elif agenda.tipo == "PET" or agenda.tipo == "CAMARA_GAMMA": duracion_slot = 60
        elif agenda.tipo == "ELECTRO_MAPEO": duracion_slot = 60
        elif agenda.tipo == "QUIMIOTERAPIA":
            duracion_slot = 60
            capacity = 7
        else: duracion_slot = 15

    # Definir rango horario (ej: 8:00 a 20:00)
    hora_inicio = datetime.combine(fecha, time(8, 0))
    hora_fin = datetime.combine(fecha, time(20, 0))

    # Buscar turnos existentes para ese día
    turnos = db.query(Turno).filter(
        Turno.agenda_id == agenda_id,
        Turno.fecha >= hora_inicio,
        Turno.fecha < hora_fin,
        Turno.estado != "cancelado"
    ).all()

    slots = []
    current_time = hora_inicio

    while current_time < hora_fin:
        slot_end = current_time + timedelta(minutes=duracion_slot)
        
        # Buscar turnos que ocupen este slot
        turnos_en_slot = []
        for t in turnos:
            t_inicio = t.fecha
            t_duracion = t.duracion if t.duracion else 15
            t_fin = t_inicio + timedelta(minutes=t_duracion)

            # Solapamiento: (StartA < EndB) and (EndA > StartB)
            if current_time < t_fin and slot_end > t_inicio:
                turnos_en_slot.append(t)
        
        # Generar slots según capacidad
        # Primero llenamos con los turnos existentes
        for i in range(capacity):
            slot_data = {
                "hora": current_time.strftime("%H:%M"),
                "fecha": current_time.isoformat(),
                "disponible": True,
                "turno": None
            }

            if i < len(turnos_en_slot):
                # Slot ocupado por un turno
                turno_ocupante = turnos_en_slot[i]
                slot_data["disponible"] = False
                slot_data["turno"] = {
                    "id": turno_ocupante.id,
                    "paciente_id": turno_ocupante.paciente_id,
                    "paciente": {
                        "nombre": turno_ocupante.paciente.nombre,
                        "apellido": turno_ocupante.paciente.apellido,
                        "id": turno_ocupante.paciente.id
                    } if turno_ocupante.paciente else None,
                    "estado": turno_ocupante.estado,
                    "estado": turno_ocupante.estado,
                    "practicas": [{"nombre": p.nombre, "id": p.id} for p in turno_ocupante.practicas],
                    "recordatorio_enviado": turno_ocupante.recordatorio_enviado # ✅ Para el check de WhatsApp
                }
            
            slots.append(slot_data)

        current_time = slot_end

    return slots
