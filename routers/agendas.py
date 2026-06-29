from datetime import date, datetime, timedelta, time
import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from database import get_db
from models.agenda import Agenda
from models.turno import Turno
from models.practica import Practica
from models.user import User
from auth.jwt import get_current_user
from services.turno_service import calculate_duration

router = APIRouter(prefix="/agendas", tags=["Agendas"])

@router.get("/")
def listar_agendas(db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    """
    Lista las agendas permitidas para el usuario actual.
    Regla: ADMIN ve todo. Otros ven las agendas vinculadas en la relación Many-to-Many.
    """
    username = current_user["username"]
    role = current_user["role"]
    
    # 1. ADMIN Bypass: See everything
    if role == "ADMIN":
        logging.info(f"PERM: Usuario {username} (ADMIN) tiene acceso total a todas las agendas.")
        return db.query(Agenda).all()
    
    # 2. Fetch User metadata
    db_user = db.query(User).filter(User.username == username).first()
    if not db_user:
        logging.warning(f"PERM: Usuario {username} no encontrado en base de datos.")
        return []
    
    # 3. Collect Agendas from Many-to-Many relationship (Unified Source)
    result = list(db_user.agendas)
    
    # Log results
    logging.info(f"PERM: Decision para {username} (Role: {role}): Assigned Agendas Count: {len(result)}")
    
    # 4. Fallback for Medicos (Only if NO agendas were found by assignment)
    # This remains as a safety net for automatically matching doctors by name if not explicitly linked.
    if not result and role == "MEDICO":
        search_term = f"%{username}%"
        fallback_agendas = db.query(Agenda).filter(Agenda.profesional.ilike(search_term)).all()
        if fallback_agendas:
            logging.info(f"PERM: Usando fallback por nombre para Médico {username}. Encontrados: {len(fallback_agendas)}")
            result = fallback_agendas
        
    return result

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
        # Default de la base de datos si existe, sino fallback por tipo
        duracion_slot = agenda.slot_minutos if agenda.slot_minutos else 15
        
        if agenda.tipo == "ECOGRAFIA": duracion_slot = 30
        elif agenda.tipo == "TOMOGRAFIA": duracion_slot = 20
        elif agenda.tipo == "RESONANCIA": duracion_slot = 30
        elif agenda.tipo == "CONSULTA_MEDICA": duracion_slot = 20
        elif agenda.tipo == "PET" or agenda.tipo == "CAMARA_GAMMA": duracion_slot = 60
        elif agenda.tipo == "ELECTRO_MAPEO": duracion_slot = 60
        elif agenda.tipo == "QUIMIOTERAPIA":
            duracion_slot = 60
            capacity = 7
        elif agenda.tipo == "RADIOTERAPIA":
            duracion_slot = agenda.slot_minutos if agenda.slot_minutos else 10 # 10 is the new standard

    # Definir rango horario (ej: 7:00 a 22:00)
    hora_inicio = datetime.combine(fecha, time(7, 0))
    hora_fin = datetime.combine(fecha + timedelta(days=1), time(0, 0))

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

            # Solapamiento:
            if agenda.tipo == "RADIOTERAPIA" or agenda_id in [3, 4]:
                # Lógica quirúrgica para Radioterapia (Evita duplicados visuales por desalineación)
                overlap_mins = (min(slot_end, t_fin) - max(current_time, t_inicio)).total_seconds() / 60
                es_inicio = (t_inicio >= current_time and t_inicio < slot_end)
                es_solapamiento_mayoritario = (overlap_mins > (duracion_slot / 2))
                
                if es_inicio or es_solapamiento_mayoritario:
                    turnos_en_slot.append(t)
            else:
                # Lógica estándar para el resto de las agendas
                if current_time < t_fin and slot_end > t_inicio:
                    turnos_en_slot.append(t)
        
        # Generar slots según capacidad
        # Primero llenamos con los turnos existentes
        # 🟢 FIX: Si hay más turnos que la capacidad, los mostramos igual (overflow)
        # La estructura ahora soportará una lista de turnos en el frontend si es necesario, 
        # pero para mantener compatibilidad, el "turno" principal será el primero, 
        # y agregaremos un campo "turnos_adicionales" o simplemente retornaremos una lista si cambiamos el frontend.
        
        # ESTRATEGIA: Mantenemos la estructura de slots por horarios fijos.
        # Si capacity=1 pero hay 2 turnos, el loop de 'i in range(capacity)' solo tomaría 1.
        # CAMBIO: Iteramos sobre MAX(capacity, len(turnos_en_slot)) para no perder ninguno.
        
        max_slots = max(capacity, len(turnos_en_slot))
        
        for i in range(max_slots):
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
                        "id": turno_ocupante.paciente.id,
                        "dni": turno_ocupante.paciente.dni
                    } if turno_ocupante.paciente else None,
                    "estado": turno_ocupante.estado,
                    "agenda_id": turno_ocupante.agenda_id,
                    "duracion": turno_ocupante.duracion,
                    "medico_derivante_id": turno_ocupante.medico_derivante_id,
                    "patologia": turno_ocupante.patologia,
                    "observaciones": turno_ocupante.observaciones,
                    "practicas": [{"nombre": p.nombre, "id": p.id} for p in turno_ocupante.practicas],
                    "recordatorio_enviado": turno_ocupante.recordatorio_enviado
                }
            
            # Solo agregamos slots vacíos si estamos dentro de la capacidad nominal
            # Si estamos en overflow (i >= capacity), solo agregamos si hay turno real.
            if i < capacity or slot_data["turno"] is not None:
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
    profesional = agenda.nombre if agenda.tipo == "MEDICO" else None

    nueva_agenda = Agenda(
        nombre=agenda.nombre,
        tipo=agenda.tipo,
        slot_minutos=agenda.slot_minutos,
        activo=agenda.activo,
        profesional=profesional
    )
    
    # 🛡️ Sync permissions if user_ids are provided
    if agenda.allowed_user_ids:
        permitted_users = db.query(User).filter(User.id.in_(agenda.allowed_user_ids)).all()
        nueva_agenda.usuarios_permitidos = permitted_users

    db.add(nueva_agenda)
    db.commit()
    db.refresh(nueva_agenda)
    
    # Manual conversion for Pydantic (or relationship will handle it if mapped)
    response = AgendaOut.from_orm(nueva_agenda)
    response.allowed_user_ids = [u.id for u in nueva_agenda.usuarios_permitidos]
    return response


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
    
    # 🛡️ Sync permissions
    if agenda_update.allowed_user_ids is not None:
        permitted_users = db.query(User).filter(User.id.in_(agenda_update.allowed_user_ids)).all()
        db_agenda.usuarios_permitidos = permitted_users

    db.commit()
    db.refresh(db_agenda)
    
    response = AgendaOut.from_orm(db_agenda)
    response.allowed_user_ids = [u.id for u in db_agenda.usuarios_permitidos]
    return response


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
