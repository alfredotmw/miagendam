# routers/turnos.py

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

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

@router.post("/", response_model=TurnoOut)
def crear_turno(turno_in: TurnoCreate, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
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
    
    try:
        duracion = calculate_duration(agenda.tipo, practicas, turno_in.duracion_custom)
    except HTTPException as e:
        raise e

    # Verificar disponibilidad
    check_availability(db, agenda.id, turno_in.fecha, duracion, agenda.tipo)

    # Manejo de Médico Derivante
    medico_id = turno_in.medico_derivante_id
    
    # Si no viene ID pero viene nombre, buscamos o creamos
    if not medico_id and turno_in.medico_derivante_nombre:
        nombre_medico = turno_in.medico_derivante_nombre.strip().upper()
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
        fecha=turno_in.fecha,
        hora=turno_in.hora,
        duracion=duracion,
        paciente_id=turno_in.paciente_id,
        agenda_id=turno_in.agenda_id,
        medico_derivante_id=medico_id, # Asignamos el médico
        estado=turno_in.estado,
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


@router.get("/", response_model=List[TurnoOut])
def listar_turnos(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    paciente_id: Optional[int] = Query(default=None),
    agenda_id: Optional[int] = Query(default=None),
    estado: Optional[str] = Query(default=None),
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

    turnos = query.order_by(Turno.fecha).offset(offset).limit(limit).all()
    return turnos

from schemas.turno import TurnoUpdate

@router.patch("/{turno_id}", response_model=TurnoOut)
def actualizar_turno(turno_id: int, turno_in: TurnoUpdate, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    turno = db.get(Turno, turno_id)
    if not turno:
        raise HTTPException(status_code=404, detail="Turno no encontrado")

    if turno_in.fecha is not None:
        turno.fecha = turno_in.fecha
    if turno_in.hora is not None:
        turno.hora = turno_in.hora
    if turno_in.estado is not None:
        turno.estado = turno_in.estado
    if turno_in.duracion is not None:
        turno.duracion = turno_in.duracion
    if turno_in.medico_derivante_id is not None:
        turno.medico_derivante_id = turno_in.medico_derivante_id

    db.commit()
    db.refresh(turno)
    return turno


