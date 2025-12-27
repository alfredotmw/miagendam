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


# ➕ Crear Agenda (Solo ADMIN)
from schemas.agenda import AgendaCreate, AgendaOut, AgendaUpdate
from auth.jwt import require_roles

@router.post("/", response_model=AgendaOut)
def create_agenda(
    agenda: AgendaCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_roles(["ADMIN"]))
):
    # Professional is automatically set to the Agenda Name for simplicity if not provided,
    # or we can extract it. Since schema doesn't have 'profesional', we'll assume name is descriptive enough 
    # OR update schema. For now, let's use name as profesional if type is MEDICO.
    
    profesional = agenda.nombre if agenda.tipo == "MEDICO" else None

    nueva_agenda = Agenda(
        nombre=agenda.nombre,
        tipo=agenda.tipo,
        slot_minutos=agenda.slot_minutos,
        activo=1 if agenda.activo else 0, # Convert bool to int
        profesional=profesional
    )
    db.add(nueva_agenda)
    db.commit()
    db.refresh(nueva_agenda)
    return nueva_agenda


@router.put("/{agenda_id}", response_model=AgendaOut)
def update_agenda(
    agenda_id: int,
    agenda_update: AgendaUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_roles(["ADMIN"]))
):
    db_agenda = db.get(Agenda, agenda_id)
    if not db_agenda:
        raise HTTPException(status_code=404, detail="Agenda no encontrada")

    if agenda_update.nombre is not None: db_agenda.nombre = agenda_update.nombre
    if agenda_update.tipo is not None: db_agenda.tipo = agenda_update.tipo
    if agenda_update.slot_minutos is not None: db_agenda.slot_minutos = agenda_update.slot_minutos
    if agenda_update.activo is not None: db_agenda.activo = agenda_update.activo
    
    db.commit()
    db.refresh(db_agenda)
    return db_agenda


@router.delete("/{agenda_id}", status_code=204)
def delete_agenda(
    agenda_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_roles(["ADMIN"]))
):
    db_agenda = db.get(Agenda, agenda_id)
    if not db_agenda:
        raise HTTPException(status_code=404, detail="Agenda no encontrada")

    # Optional: Check if it has future appointments before deleting?
    # For now, just allow delete. Cascades usually handle Turnos, or they stick around orphaned.
    db.delete(db_agenda)
    db.commit()
    return None
