from datetime import timedelta, datetime
from sqlalchemy.orm import Session
from fastapi import HTTPException
from models.turno import Turno
from models.practica import CategoriaPractica

def calculate_duration(agenda_tipo: str, practicas: list, custom_duration: int = None) -> int:
    """
    Calcula la duración del turno basándose en las reglas de negocio.
    """
    
    # Reglas para Radioterapia (San Martín y Colombia)
    if agenda_tipo == "RADIOTERAPIA":
        if custom_duration not in [10, 20]:
            raise HTTPException(status_code=400, detail="Para Radioterapia la duración debe ser 10 o 20 minutos.")
        return custom_duration

    # Reglas para Cámara Gamma y PET
    if agenda_tipo in ["CAMARA_GAMMA", "PET"]:
        return 60 # 1 hora

    # Reglas para Electro y Mapeos
    if agenda_tipo == "ELECTRO_MAPEO":
        return 60 # 1 hora

    # Reglas para Ecografías
    if agenda_tipo == "ECOGRAFIA":
        return 30 # 30 minutos fijo

    # Reglas para Quimioterapia
    if agenda_tipo == "QUIMIOTERAPIA":
        return 60 # 1 hora

    # Reglas para Consultas Médicas
    if agenda_tipo == "CONSULTA_MEDICA":
        return 20 # 20 minutos

    # Reglas para Tomografía y RX (agenda mixta o específica)
    # Asumimos que la agenda puede tener tipo "TOMOGRAFIA" o "RADIOGRAFIA" o un genérico "IMAGENES"
    # Pero según el seed, tenemos "TOMOGRAFIA" para "TOMOGRAFIAS Y RX"
    if agenda_tipo == "TOMOGRAFIA":
        tiene_tomo = any(p.categoria == CategoriaPractica.TOMOGRAFIA for p in practicas)
        tiene_rx = any(p.categoria == CategoriaPractica.RADIOGRAFIA for p in practicas)

        if tiene_tomo and tiene_rx:
            return 30
        if tiene_tomo:
            return 20
        if tiene_rx:
            return 15
        
        # Default si no matchea nada (raro)
        return 15

    # Default general
    return 15

def check_availability(db: Session, agenda_id: int, fecha_hora_inicio: datetime, duracion_minutos: int, agenda_tipo: str):
    """
    Verifica si hay disponibilidad para el turno.
    Maneja la capacidad de sillones para Quimioterapia.
    """
    validate_time_rules(fecha_hora_inicio.strftime("%H:%M:%S"))
    fecha_hora_fin = fecha_hora_inicio + timedelta(minutes=duracion_minutos)

    # Buscar turnos que se solapen en esa agenda
    # Un turno se solapa si:
    # (InicioA < FinB) y (FinA > InicioB)
    turnos_solapados = db.query(Turno).filter(
        Turno.agenda_id == agenda_id,
        Turno.estado != "cancelado",
        Turno.fecha < fecha_hora_fin, # Inicio del turno existente es menor al fin del nuevo
        # Aquí hay un detalle: Turno.fecha es el inicio. Necesitamos saber la duración de los turnos existentes.
        # Como acabamos de agregar la columna duración, asumimos que los turnos viejos podrían no tenerla.
        # Para simplificar la query en SQL, idealmente tendríamos la fecha de fin guardada.
        # Pero podemos hacerlo calculando en Python o asumiendo una duración standard si es null.
    ).all()

    count_solapados = 0
    for t in turnos_solapados:
        # Calcular fin del turno existente
        duracion_t = t.duracion if t.duracion else 15 # Fallback
        t_inicio = t.fecha
        t_fin = t_inicio + timedelta(minutes=duracion_t)

        # Chequear solapamiento exacto
        if t_inicio < fecha_hora_fin and t_fin > fecha_hora_inicio:
            count_solapados += 1

    # Capacidad máxima
    capacidad_maxima = 1 # Por defecto 1 paciente por vez (consultorio, equipos)

    if agenda_tipo == "QUIMIOTERAPIA":
        capacidad_maxima = 7 # 7 sillones
    
    # 🟢 FIX: Enforce strict single capacity for PET/GAMMA (Just in case logic changes)
    if agenda_tipo in ["PET", "CAMARA_GAMMA"]:
        capacidad_maxima = 1

    if count_solapados >= capacidad_maxima:
        raise HTTPException(
            status_code=400, 
            detail=f"⚠️ HORARIO OCUPADO: Ya existe un turno asignado en este horario. (Capacidad máxima: {capacidad_maxima})"
        )

def validate_time_rules(hora: str):
    """
    Valida que el horario esté dentro del rango comercial (07:00 a 21:00).
    Bloquea explícitamente el horario 00:00:00.
    """
    try:
        # Formatos posibles: "HH:MM", "HH:MM:SS"
        # Si viene "00:00:00" o "00:00", lo bloqueamos
        if hora.startswith("00:00"):
            raise HTTPException(status_code=400, detail="⚠️ Horario no habilitado (00:00 es inválido)")

        h = int(hora.split(':')[0])
        if h < 7 or h >= 21:
            raise HTTPException(status_code=400, detail="⚠️ Horario no habilitado (Rango permitido: 07:00–21:00)")
    except (ValueError, IndexError):
        raise HTTPException(status_code=400, detail="⚠️ Formato de hora inválido")
    return True

def validate_duplicate_rules(db: Session, paciente_id: int, agenda_id: int, fecha: datetime, practicas_ids: list, exclude_turno_id: int = None):
    """
    Bloquea mismo paciente + misma agenda + misma práctica + mismo día.
    Especialmente crítico para Quimioterapia.
    """
    from models.turno_practica import TurnoPractica
    
    # Query: Buscar turnos del paciente en esa agenda para ese día (sin contar el turno actual si es update)
    query = db.query(Turno).filter(
        Turno.paciente_id == paciente_id,
        Turno.agenda_id == agenda_id,
        Turno.fecha >= datetime.combine(fecha.date(), datetime.min.time()),
        Turno.fecha <= datetime.combine(fecha.date(), datetime.max.time()),
        Turno.estado != "cancelado"
    )
    
    if exclude_turno_id:
        query = query.filter(Turno.id != exclude_turno_id)
        
    turnos_dia = query.all()
    
    for t in turnos_dia:
        # Chequear prácticas
        t_practicas_ids = [p.id for p in t.practicas]
        # Si alguno de los practicas_ids solicitados ya está en este turno, es un duplicado
        duplicadas = set(practicas_ids).intersection(set(t_practicas_ids))
        if duplicadas:
             raise HTTPException(
                status_code=409, 
                detail="⚠️ Turno duplicado: el paciente ya tiene esa práctica en esa agenda para esa fecha."
            )
    return True

def check_availability_boolean(db: Session, agenda_id: int, fecha_hora_inicio: datetime, duracion_minutos: int, agenda_tipo: str) -> bool:
    """
    Versión booleana de check_availability. Retorna True si hay lugar, False si no.
    """
    try:
        # 🟢 FIX: For availability map (slots), we want to return FALSE if strictly full.
        # But we also want to allow "Overflow" viewing in Agenda, but NOT new booking.
        # This function is used by 'get_available_slots' (Booking UI). So it MUST return False if full.
        check_availability(db, agenda_id, fecha_hora_inicio, duracion_minutos, agenda_tipo)
        return True
    except HTTPException:
        return False

def validate_date_rules(fecha: datetime):
    """
    Valida reglas de negocio generales para fechas.
    - Rechaza Domingos (weekday == 6)
    """
    if fecha.weekday() == 6: # 0=Monday, 6=Sunday
        raise HTTPException(status_code=400, detail="No se pueden agendar turnos los días Domingo.")
    return True
