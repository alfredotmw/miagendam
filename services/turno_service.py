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
            detail=f"⚠️ [V3] HORARIO OCUPADO: Ya existe un turno asignado en este horario. (Capacidad máxima: {capacidad_maxima})"
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
        if h < 7 or h >= 24:
            raise HTTPException(status_code=400, detail="⚠️ Horario no habilitado (Rango permitido: 07:00–23:59)")
    except (ValueError, IndexError):
        raise HTTPException(status_code=400, detail="⚠️ Formato de hora inválido")
    return True

def validate_duplicate_rules(db: Session, paciente_id: int, agenda_id: int, fecha: datetime, practicas_ids: list, exclude_turno_id: int = None, patologia: str = None):
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
        
    turnos_existentes = query.all()

    # 🟢 EXCEPCIÓN RADIOTERAPIA: Permitir duplicado si es distinta patología
    from models.agenda import Agenda
    agenda = db.get(Agenda, agenda_id)
    es_radioterapia = agenda and (agenda.tipo == "RADIOTERAPIA" or agenda_id in [3, 4]) # IDs 3 y 4 son Radioterapia en seed

    for t in turnos_existentes:
        # Check if any practice matches
        p_existentes_ids = [p.id for p in t.practicas]
        
        # Find common practices between the new turn and existing turn
        duplicadas = set(practicas_ids).intersection(set(p_existentes_ids))
        
        if duplicadas:
            if es_radioterapia:
                # En Radioterapia, permitimos misma práctica el mismo día SOLO SI es distinta patología
                # Normalizamos patologías para comparación
                patologia_existente = t.patologia.strip().upper() if t.patologia else ""
                patologia_nueva = patologia.strip().upper() if patologia else ""

                if patologia_existente == patologia_nueva and patologia_nueva != "":
                    # Si la patología es la misma (y no está vacía), es un duplicado funcional
                    raise HTTPException(
                        status_code=409,
                        detail=f"⚠️ Turno duplicado: el paciente ya tiene la práctica {list(duplicadas)} en esa agenda para esa fecha y misma patología ({patologia_nueva})."
                    )
                # Si las patologías son diferentes, se permite el duplicado en Radioterapia
                # Si la patología es vacía en ambos, se considera duplicado (no hay distinción)
                elif patologia_existente == "" and patologia_nueva == "":
                    raise HTTPException(
                        status_code=409,
                        detail=f"⚠️ Turno duplicado: el paciente ya tiene la práctica {list(duplicadas)} en esa agenda para esa fecha. (Patología no especificada)."
                    )
            else:
                # Para otras agendas, cualquier práctica duplicada es un error
                raise HTTPException(
                    status_code=409, 
                    detail=f"⚠️ Turno duplicado: el paciente ya tiene la práctica {list(duplicadas)} en esa agenda para esa fecha."
                )
    return True

def check_availability_boolean(db: Session, agenda_id: int, fecha_hora_inicio: datetime, duracion_minutos: int, agenda_tipo: str, paciente_id: int = None, practicas: list = None, patologia: str = None) -> bool:
    """
    Versión booleana de check_availability. Retorna True si hay lugar, False si no.
    Si se provee paciente_id, aplica las reglas de excepción de Radioterapia.
    """
    try:
        check_availability(db, agenda_id, fecha_hora_inicio, duracion_minutos, agenda_tipo)
        return True
    except HTTPException as e:
        if paciente_id and e.status_code == 400 and "HORARIO OCUPADO" in str(e.detail):
            # Si falla por ocupación, verificamos si es una excepción válida para este paciente en Radioterapia
            # Nota: Necesitamos cargar las prácticas y patología si no vienen, pero para el mapa de slots 
            # solemos tenerlas en el contexto de la reserva.
            if agenda_tipo == "RADIOTERAPIA" and practicas:
                from services.turno_service import validate_same_patient_overlap
                try:
                    # Primero verificar que el conflicto sea EXCLUSIVAMENTE con el mismo paciente
                    fecha_hora_fin = fecha_hora_inicio + timedelta(minutes=duracion_minutos)
                    otros_pacientes_solapados = db.query(Turno).filter(
                        Turno.agenda_id == agenda_id,
                        Turno.estado.notin_(["CANCELADO", "cancelado", "ANULADO", "anulado", "INACTIVO", "inactivo"]),
                        Turno.fecha < fecha_hora_fin,
                        Turno.paciente_id != paciente_id
                    ).all()

                    capacidad_real_otros = 0
                    for t in otros_pacientes_solapados:
                        t_duracion = t.duracion if t.duracion else 15
                        if t.fecha < fecha_hora_fin and (t.fecha + timedelta(minutes=t_duracion)) > fecha_hora_inicio:
                            capacidad_real_otros += 1
                    
                    if capacidad_real_otros >= 1: # Radioterapia siempre es 1
                        return False

                    return validate_same_patient_overlap(db, paciente_id, agenda_id, fecha_hora_inicio, duracion_minutos, practicas, patologia)
                except HTTPException: # Captura el 409 de duplicado funcional
                    return False
        return False

def validate_date_rules(fecha: datetime):
    """
    Valida reglas de negocio generales para fechas.
    - Rechaza Domingos (weekday == 6)
    """
    if fecha.weekday() == 6: # 0=Monday, 6=Sunday
        raise HTTPException(status_code=400, detail="No se pueden agendar turnos los días Domingo.")
    return True

def get_agenda_sede(agenda) -> str:
    """
    Identifica la sede de la agenda de forma normalizada (San Martin vs Colombia).
    """
    if not agenda: return "OTRA"
    
    nombre_alto = agenda.nombre.upper()
    if agenda.id == 3 or "SAN MARTIN" in nombre_alto or "S.M" in nombre_alto:
        return "SAN MARTIN"
    if agenda.id == 4 or "COLOMBIA" in nombre_alto:
        return "COLOMBIA"
    return "OTRA"

def resolve_treatment_type(practicas: list) -> str:
    """
    Resuelve el tipo de tratamiento (técnica) basándose en las prácticas.
    """
    import unicodedata
    def normalize_text(text):
        return ''.join(c for c in unicodedata.normalize('NFD', text) if unicodedata.category(c) != 'Mn').upper()

    for p in practicas:
        p_name = normalize_text(p.nombre)
        if "IMRT" in p_name:
            return "IMRT"
        if "3D" in p_name or "TRIDIMENSIONAL" in p_name:
            return "RT 3D"
    
    return "OTRO"

def validate_same_patient_overlap(db: Session, paciente_id: int, agenda_id: int, fecha_hora: datetime, duration: int, practicas: list, patologia: str):
    """
    Versión diagnóstica completa para producción.
    Lanza errores detallados para entender por qué se bloquea.
    """
    from models.agenda import Agenda
    agenda = db.get(Agenda, agenda_id)
    tipo_alto = agenda.tipo.upper() if agenda and agenda.tipo else ""
    
    if not agenda or tipo_alto != "RADIOTERAPIA":
        # 🟢 DIAGNÓSTICO: Si no es Radioterapia, no aplicamos la excepción de mismo paciente
        # Pero devolvemos una pista si es que pensábamos que era Radio.
        # return False  <-- Esto hacía que se mostrara el error original sin pistas
        raise HTTPException(status_code=400, detail=f"⚠️ Bloqueo: La agenda {agenda_id} no es de tipo RADIOTERAPIA (Tipo detectado: '{tipo_alto}')")
    
    new_treatment = resolve_treatment_type(practicas)
    new_pato = patologia.strip().upper() if patologia else ""
    fecha_fin = fecha_hora + timedelta(minutes=duration)

    # 1. Buscar turnos activos del mismo paciente
    query = db.query(Turno).filter(
        Turno.paciente_id == paciente_id,
        Turno.estado.notin_(["CANCELADO", "cancelado", "ANULADO", "anulado", "INACTIVO", "inactivo"]),
        Turno.fecha < fecha_fin
    )
    overlapping_turns = query.all()
    
    if not overlapping_turns:
        # Esto es raro si check_availability dijo que había conflicto con este paciente
        raise HTTPException(status_code=400, detail=f"⚠️ Diag: No se encontraron otros turnos para paciente {paciente_id} en query (Fin check: {fecha_fin})")

    diag_log = []
    has_valid_overlap = False
    
    for t in overlapping_turns:
        t_duracion = t.duracion if t.duracion else 15
        t_inicio = t.fecha
        t_fin = t_inicio + timedelta(minutes=t_duracion)
        
        # 2. Verificar solapamiento real
        if t_inicio < fecha_fin and t_fin > fecha_hora:
            # Identificar servicio del turno encontrado
            t_agenda = t.agenda # Asumimos relación cargada o lazy-load
            es_radio_existente = (t_agenda.tipo == "RADIOTERAPIA" or "RADIOTERAPIA" in t_agenda.nombre.upper())
            
            if not es_radio_existente:
                diag_log.append(f"Solapa con {t_agenda.tipo}-ID:{t.id}-OK")
                has_valid_overlap = True
                continue
            
            # Si es Radioterapia, comparar patología y técnica
            old_treatment = resolve_treatment_type(t.practicas)
            old_pato = t.patologia.strip().upper() if t.patologia else ""
            
            if old_pato == new_pato and old_treatment == new_treatment:
                diag_log.append(f"DUPLICADO-{old_treatment}-{old_pato}")
                # Seguimos el loop por si hay otros turnos que SÍ sean válidos (ej: una Quimio solapada)
            else:
                diag_log.append(f"OverlapValido-{old_treatment}-{old_pato}-OK")
                has_valid_overlap = True
        else:
            diag_log.append(f"FueraRango-ID:{t.id}")
    
    if not has_valid_overlap:
        raise HTTPException(status_code=400, detail=f"⚠️ Bloqueo persistente: {', '.join(diag_log)}. Nuevo: {new_treatment}/{new_pato}")

    return True
