# routers/turnos.py

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from database import get_db
from models.turno import Turno
from models.paciente import Paciente
from models.agenda import Agenda
from models.practica import Practica
from models.turno_practica import TurnoPractica

from schemas.turno import TurnoCreate, TurnoOut

router = APIRouter(
    prefix="/turnos",
    tags=["Turnos"],
)

from auth.jwt import get_current_user

@router.get("/patologias", response_model=List[str])
def get_patologias(db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    # Default pathologies
    defaults = ["Mama", "Pulmón", "Próstata", "Colon", "Cerebro", "Recto", "Otro"]
    
    # Fetch distinct pathologies from DB
    db_patologias = db.query(Turno.patologia).distinct().filter(Turno.patologia != None).all()
    
    # Flatten list and filter empty strings
    custom_patologias = [p[0] for p in db_patologias if p[0]]
    
    # Merge and deduplicate
    all_patologias = sorted(list(set(defaults + custom_patologias)))
    
    return all_patologias


@router.post("/", response_model=TurnoOut)
def crear_turno(turno_in: TurnoCreate, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    try:
        # Verificamos que el paciente exista
        paciente = db.get(Paciente, turno_in.paciente_id)
        if not paciente:
            raise HTTPException(status_code=404, detail="Paciente no encontrado")

        # Verificamos que la agenda exista
        agenda = db.get(Agenda, turno_in.agenda_id)
        if not agenda:
            raise HTTPException(status_code=404, detail="Agenda no encontrada")

        # Verificamos que todas las prácticas existan
        if not turno_in.practicas_ids:
            raise HTTPException(status_code=400, detail="Debe seleccionar al menos una práctica")

        practicas = db.query(Practica).filter(Practica.id.in_(turno_in.practicas_ids)).all()
        if len(practicas) != len(set(turno_in.practicas_ids)):
            raise HTTPException(status_code=400, detail="Una o más prácticas no existen")

        # Calcular duración
        from services.turno_service import calculate_duration, check_availability
        from models.medico import MedicoDerivante # Importar modelo
        
        duracion = calculate_duration(agenda.tipo, practicas, turno_in.duracion_custom)

        # Combinar fecha y hora para tener el datetime correcto
        # turno_in.fecha viene como datetime (pero con hora 00:00 si viene de un date input)
        # turno_in.hora viene como string "HH:MM" o "HH:MM:SS"
        try:
            h, m = map(int, turno_in.hora.split(':')[:2])
            fecha_hora_real = turno_in.fecha.replace(hour=h, minute=m)
        except Exception:
             raise HTTPException(status_code=400, detail="Formato de hora inválido")

        # Verificar disponibilidad con la fecha y hora REAL
        check_availability(db, agenda.id, fecha_hora_real, duracion, agenda.tipo)

        # Manejo de Médico Derivante (OBLIGATORIO)
        medico_id = turno_in.medico_derivante_id
        
        if not medico_id and not turno_in.medico_derivante_nombre:
            raise HTTPException(status_code=400, detail="El Médico Derivante es obligatorio")

        # Si no viene ID pero viene nombre, buscamos o creamos
        if not medico_id and turno_in.medico_derivante_nombre:
            nombre_medico = turno_in.medico_derivante_nombre.strip().upper() # FORCE UPPERCASE
            medico_existente = db.query(MedicoDerivante).filter(MedicoDerivante.nombre == nombre_medico).first()
            
            if medico_existente:
                medico_id = medico_existente.id
            else:
                # Crear nuevo médico derivante
                nuevo_medico = MedicoDerivante(nombre=nombre_medico)
                db.add(nuevo_medico)
                db.commit()
                db.refresh(nuevo_medico)
                medico_id = nuevo_medico.id

        # Creamos el turno
        nuevo_turno = Turno(
            fecha=fecha_hora_real, # Guardamos el datetime completo
            hora=turno_in.hora,
            duracion=duracion,
            paciente_id=turno_in.paciente_id,
            agenda_id=turno_in.agenda_id,
            medico_derivante_id=medico_id, # Asignamos el médico
            estado=turno_in.estado.upper() if turno_in.estado else "PENDIENTE",
        )
        db.add(nuevo_turno)
        db.flush()  # para obtener nuevo_turno.id sin hacer commit todavía

        # Asociamos las prácticas al turno en la tabla intermedia
        for p in practicas:
            tp = TurnoPractica(
                turno_id=nuevo_turno.id,
                practica_id=p.id
            )
            db.add(tp)

        db.commit()
        db.refresh(nuevo_turno)

        return nuevo_turno
    except HTTPException as e:
        raise e
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


@router.get("/", response_model=List[TurnoOut])
def listar_turnos(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    paciente_id: Optional[int] = Query(default=None),
    agenda_id: Optional[int] = Query(default=None),
    estado: Optional[str] = Query(default=None),
    paciente_dni: Optional[str] = Query(default=None), # Nuevo filtro
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
):
    query = db.query(Turno)

    if paciente_id is not None:
        query = query.filter(Turno.paciente_id == paciente_id)
    if agenda_id is not None:
        query = query.filter(Turno.agenda_id == agenda_id)
    if estado is not None:
        query = query.filter(Turno.estado == estado)
    
    # 🟢 Nuevo filtro por DNI
    if paciente_dni is not None:
        query = query.join(Paciente).filter(Paciente.dni == paciente_dni)

    turnos = query.order_by(Turno.fecha).offset(offset).limit(limit).all()
    return turnos

from schemas.turno import TurnoUpdate

@router.patch("/{turno_id}", response_model=TurnoOut)
def actualizar_turno(turno_id: int, turno_in: TurnoUpdate, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    print(f"RECIBIDO PATCH para turno {turno_id} con datos: {turno_in}")
    turno = db.get(Turno, turno_id)
    if not turno:
        raise HTTPException(status_code=404, detail="Turno no encontrado")

    # Actualización de Fecha y Hora (Combinadas)
    if turno_in.fecha is not None or turno_in.hora is not None:
        # Usar la nueva fecha o la existente
        nueva_fecha_base = turno_in.fecha if turno_in.fecha is not None else turno.fecha
        # Usar la nueva hora o la existente
        nueva_hora_str = turno_in.hora if turno_in.hora is not None else turno.hora

        try:
            h, m = map(int, nueva_hora_str.split(':')[:2])
            
            # 🟢 FIX: Usar datetime.combine para evitar problemas de timezone o residuos de hora
            from datetime import time as dt_time
            fecha_solo = nueva_fecha_base.date()
            fecha_hora_real = datetime.combine(fecha_solo, dt_time(h, m))
            
            turno.fecha = fecha_hora_real
            turno.hora = nueva_hora_str
        except Exception as e:
             print(f"Error actualizando fecha/hora: {e}")
             raise HTTPException(status_code=400, detail="Formato de hora inválido")
    if turno_in.estado is not None:
        turno.estado = turno_in.estado.upper()
    if turno_in.duracion is not None:
        turno.duracion = turno_in.duracion
    if turno_in.medico_derivante_id is not None:
        turno.medico_derivante_id = turno_in.medico_derivante_id
    if turno_in.patologia is not None:
        turno.patologia = turno_in.patologia

    db.commit()
    db.refresh(turno)
    return turno



@router.get("/available_slots")
def get_available_slots(
    agenda_id: int,
    fecha: str, # YYYY-MM-DD
    duracion: int,
    practicas_ids: List[int] = Query(...),
    days_count: int = Query(default=1),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    from datetime import datetime, timedelta, time
    from services.turno_service import check_availability_boolean

    try:
        start_date = datetime.strptime(fecha, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Formato de fecha inválido. Use YYYY-MM-DD")

    agenda = db.get(Agenda, agenda_id)
    if not agenda:
        raise HTTPException(status_code=404, detail="Agenda no encontrada")

    # Generate candidate slots (e.g., 8:00 to 20:00)
    # TODO: Make this configurable per agenda or global setting
    start_hour = 8
    end_hour = 20
    interval = 10 # minutes, granularity for search

    available_slots = []
    
    # Generate list of working days to check
    dates_to_check = []
    current_date = start_date
    while len(dates_to_check) < days_count:
        # Skip weekends
        if current_date.weekday() < 5: # 0-4 are Mon-Fri
            dates_to_check.append(current_date)
        current_date += timedelta(days=1)

    # Iterate over time slots
    current_time = datetime.combine(start_date, time(start_hour, 0))
    end_time = datetime.combine(start_date, time(end_hour, 0))

    while current_time + timedelta(minutes=duracion) <= end_time:
        slot_time = current_time.time()
        slot_str = slot_time.strftime("%H:%M")
        
        all_days_free = True
        
        for date_check in dates_to_check:
            # Construct datetime for this specific day and slot
            dt_check = datetime.combine(date_check, slot_time)
            
            # Check availability
            # We need a version of check_availability that returns Bool instead of raising
            if not check_availability_boolean(db, agenda_id, dt_check, duracion, agenda.tipo):
                all_days_free = False
                break
        
        if all_days_free:
            available_slots.append(slot_str)

        current_time += timedelta(minutes=interval)

    return available_slots

@router.get("/report", response_model=List[TurnoOut])
def get_daily_report(
    date: str, # YYYY-MM-DD
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    try:
        start_of_day = datetime.strptime(date, "%Y-%m-%d")
        # En Postgres/SQLAlchemy, para comparar fecha exacta a veces es mejor rango
        # Pero intentaremos filtro simple primero. Si fecha tiene hora, usar >= y <
        
        # Filtrar todos los turnos de ese día
        end_of_day = start_of_day.replace(hour=23, minute=59, second=59)
        
        query = db.query(Turno).filter(
            Turno.fecha >= start_of_day,
            Turno.fecha <= end_of_day
        )

        # 🟢 Optional: allow filtering by pending status if requested (not used by default yet but useful logic)
        # But for now, user just asked for a better view. The frontend filters by date.
        # Let's keep date filter but maybe we need a new param 'pending_only' later.
        # For now, let's just ensure we return the notification columns so frontend can filter.
        
        turnos = query.order_by(Turno.hora).all()
        
        return turnos
        
    except ValueError:
        raise HTTPException(status_code=400, detail="Fecha inválida")
