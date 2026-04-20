# routers/turnos.py

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta

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


from schemas.check_duplicates import CheckDuplicates

@router.post("/verificar_duplicados")
def verificar_duplicados(check: CheckDuplicates, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    """
    Verifica si un paciente ya tiene turnos activos en las fechas proporcionadas.
    Retorna una lista de alertas si hay coincidencias.
    """
    # Buscar turnos activos (no cancelados) para el paciente en las fechas dadas
    query = db.query(Turno).filter(
        Turno.paciente_id == check.paciente_id,
        Turno.estado != "CANCELADO"
    )

    if check.agenda_id:
        query = query.filter(Turno.agenda_id == check.agenda_id)

    coincidencias = query.all()
    
    # Filter in Python to avoid DB-specific complications with Cast/Date matching
    fechas_input_set = set(check.fechas)
    duplicados = []
    
    for t in coincidencias:
        if t.fecha.date() in fechas_input_set:
            duplicados.append(t.fecha.strftime("%d/%m/%Y"))
            
    if duplicados:
        fechas_str = ", ".join(sorted(list(set(duplicados))))
        return {
            "status": "alerta",
            "mensaje": f"El paciente ya tiene turnos asignados en las siguientes fechas: {fechas_str}. ¿Desea continuar y agendar turnos dobles?"
        }
    
    return {"status": "ok"}


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

        # 🟢 AUTOMATION: Pre-calculate TAC MARCACION trigger
        is_tac_marcacion_trigger = False
        import unicodedata
        def normalize_text_check(text):
            return ''.join(c for c in unicodedata.normalize('NFD', text) if unicodedata.category(c) != 'Mn').upper()

        for p in practicas:
            if "MARCACION" in normalize_text_check(p.nombre):
                is_tac_marcacion_trigger = True

        # Calcular duración
        from services.turno_service import calculate_duration, check_availability
        from models.medico import MedicoDerivante # Importar modelo
        
        duracion = calculate_duration(agenda.tipo, practicas, turno_in.duracion_custom)

        # Combinar fecha y hora para tener el datetime correcto
        try:
            h, m = map(int, turno_in.hora.split(':')[:2])
            fecha_hora_real = turno_in.fecha.replace(hour=h, minute=m)
        except Exception:
             raise HTTPException(status_code=400, detail="Formato de hora inválido")

        # 🟢 VALIDACIÓN DE REGLAS DE NEGOCIO (Rango Horario y Duplicados)
        from services.turno_service import validate_time_rules, validate_duplicate_rules, validate_date_rules
        
        # Validar Domingo
        validate_date_rules(fecha_hora_real)
        # Validar Horario Comercial (07-21)
        validate_time_rules(turno_in.hora)
        # Validar Duplicados (Mismo Paciente/Agenda/Práctica/Día)
        validate_duplicate_rules(db, turno_in.paciente_id, agenda.id, fecha_hora_real, turno_in.practicas_ids, patologia=turno_in.patologia)

        # Verificar disponibilidad con la fecha y hora REAL
        try:
            check_availability(db, agenda.id, fecha_hora_real, duracion, agenda.tipo)
        except HTTPException as e:
            # 🟢 EXCEPCIÓN RADIOTERAPIA: Capturamos cualquier error 400
            if e.status_code == 400:
                from services.turno_service import validate_same_patient_overlap
                try:
                    if validate_same_patient_overlap(db, turno_in.paciente_id, agenda.id, fecha_hora_real, duracion, practicas, turno_in.patologia):
                        pass # Permitir
                    else:
                        raise e
                except HTTPException as he:
                    raise he
                except Exception:
                    raise e
            else:
                raise e

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
            patologia=turno_in.patologia.strip().upper() if turno_in.patologia else None # ✅ Normalización a mayúsculas
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

        # db.commit()  <-- REMOVED: Commit moved to the end to ensure atomicity
        # db.refresh(nuevo_turno) <-- REMOVED
        
            
        # 🟢 AUTOMATION: Radiotherapy Registry (Create & Update)
        from models.radioterapia import SeguimientoRadioterapia
        from sqlalchemy import desc
        
        # Logic:
        # 1. Get latest record.
        # 2. Check if it's "Finished":
        #    - If fecha_fin exists AND > 60 days passed since then.
        #    - If no fecha_fin or <= 60 days -> Continued Treatment.
        
        cutoff_date = datetime.now().date() - timedelta(days=60)
        
        latest_seg = db.query(SeguimientoRadioterapia)\
            .filter(SeguimientoRadioterapia.paciente_id == turno_in.paciente_id)\
            .order_by(desc(SeguimientoRadioterapia.created_at))\
            .first()

        is_finished = False
        if latest_seg and latest_seg.fecha_fin:
            if latest_seg.fecha_fin < cutoff_date:
                is_finished = True
        
        # Determine if we should create NEW or reuse
        seguimiento = None
        if not latest_seg or (latest_seg and is_finished):
             # Create Logic applies
             pass
        else:
             # Update latest
             seguimiento = latest_seg

        # 2. Create Logic (if needed)
        if (turno_in.crear_seguimiento or is_tac_marcacion_trigger) and not seguimiento:
            # Determine Responsible from Agenda Name
            responsable = "Dr. Angel Miño" # Default fallback
            a_name = agenda.nombre.upper()
            if "DUARTE" in a_name:
                responsable = "Dra. Duarte Angelica"
            elif "MIÑO" in a_name:
                responsable = "Dr. Angel Miño"
            
            # Determine Sede
            sede = None
            if agenda.id == 3 or "SAN MARTIN" in a_name:
                sede = "San Martín"
            elif agenda.id == 4 or "COLOMBIA" in a_name:
                sede = "Colombia"
                
            # Determine Technique
            technique = None
            for p in practicas:
                p_name_upper = p.nombre.upper()
                if "IMRT" in p_name_upper:
                    technique = "IMRT"
                elif "3D" in p_name_upper or "TRIDIMENSIONAL" in p_name_upper:
                    technique = "RT 3D"
            
            # Get Derivante Name
            derivante_name = ""
            if medico_id:
                md = db.get(MedicoDerivante, medico_id)
                if md: derivante_name = md.nombre

            # 🟢 SEARCH FOR CONSULTA DE 1RA VEZ
            fecha_1ra_consulta = None
            try:
                # Search specifically for practice "CONSULTA DE 1RA VEZ"
                first_consult = db.query(Turno).join(TurnoPractica).join(Practica)\
                    .filter(Turno.paciente_id == turno_in.paciente_id)\
                    .filter(Turno.id != nuevo_turno.id)\
                    .filter(Practica.nombre == "CONSULTA DE 1RA VEZ")\
                    .order_by(Turno.fecha.desc())\
                    .first()
                
                if first_consult:
                    fecha_1ra_consulta = first_consult.fecha.date()
            except Exception as e:
                print(f"Error searching first consult: {e}")

            seguimiento = SeguimientoRadioterapia(
                paciente_id=turno_in.paciente_id,
                patologia=turno_in.patologia.strip().upper() if turno_in.patologia else None,
                medico_derivante=derivante_name,
                medico_responsable=responsable,
                sede=sede,
                tipo_tecnica=technique,
                fecha_consulta=fecha_1ra_consulta,
                created_at=datetime.now()
            )
            db.add(seguimiento)
            # db.commit() <-- Removed internal commit to rely on final commit
            # db.refresh(seguimiento)
        
        # 🟢 FIX: If we ARE reusing a tracking record, force update of Derivante/Patologia if they changed
        # This fixes the issue where old tracking info persists even if the new appointment has different data.
        elif seguimiento:
             # Logic to update persistent fields if they are different in the NEW appointment
             # This assumes the latest appointment is the source of truth for the current treatment.
             
             # 1. Update Pathology if present
             updated_persistent = False # Fix UnboundLocalError
             if turno_in.patologia:
                 pato_normalized = turno_in.patologia.strip().upper()
                 if seguimiento.patologia != pato_normalized:
                     seguimiento.patologia = pato_normalized
                     updated_persistent = True
                     
             # 2. Update Derivante if present
             if medico_id:
                 md = db.get(MedicoDerivante, medico_id)
                 if md and seguimiento.medico_derivante != md.nombre:
                     seguimiento.medico_derivante = md.nombre
                     updated_persistent = True

             # 3. Update Responsible (if agenda changed doctors)
             # Determine Responsible from Agenda Name
             responsable = "Dr. Angel Miño" # Default fallback
             a_name = agenda.nombre.upper()
             if "DUARTE" in a_name:
                 responsable = "Dra. Duarte Angelica"
             elif "MIÑO" in a_name:
                 responsable = "Dr. Angel Miño"
             
             if seguimiento.medico_responsable != responsable:
                 seguimiento.medico_responsable = responsable
                 updated_persistent = True

             if updated_persistent:
                 db.add(seguimiento)
                 # db.commit() <-- Removed internal commit

        # 3. Update Logic (if tracking exists)
        if seguimiento:
            updated = False
            
            # Check Agenda Type (Radio San Martin ID=3, Colombia ID=4, or type RADIOTERAPIA)
            is_radio_agenda = agenda.tipo == "RADIOTERAPIA" or agenda.id in [3, 4]
            
            # Check Practice (TAC de Marcación)
            is_tac_marcacion = False
            for p in practicas:
                # 🟢 FIX: Normalize Accents (Marcación -> MARCACION)
                import unicodedata
                def normalize_text(text):
                    return ''.join(c for c in unicodedata.normalize('NFD', text) if unicodedata.category(c) != 'Mn').upper()

                p_name = normalize_text(p.nombre)
                if "MARCACION" in p_name:
                    is_tac_marcacion = True
                # También si es una agenda de TOMOGRAFIA y la práctica tiene TAC
                if agenda.tipo == "TOMOGRAFIA" and "TAC" in p_name:
                     # Refuerzo: Si ya tiene seguimiento, cualquier TAC en agenda de tomografia podría ser la simulación
                     # Pero priorizamos la palabra MARCACION si existe.
                     # Si no tiene fecha_tac aun, tomamos este TAC.
                     if not seguimiento.fecha_tac:
                         is_tac_marcacion = True

            # Radiotherapy Start Date
            if is_radio_agenda:
                new_start_date = nuevo_turno.fecha.date()
                can_update_start = True
                
                # 🟢 VALIDATION: Start Date cannot be before TAC Date
                if seguimiento.fecha_tac and new_start_date < seguimiento.fecha_tac:
                    can_update_start = False
                    
                if can_update_start:
                    if not seguimiento.fecha_inicio:
                        seguimiento.fecha_inicio = new_start_date
                        updated = True
                    elif new_start_date < seguimiento.fecha_inicio:
                        seguimiento.fecha_inicio = new_start_date
                        updated = True
            
            # Simulation CT Date
            if is_tac_marcacion:
                # Si es una marcación explicita, sobreescribimos o seteamos
                # Si es un TAC generico, solo seteamos si esta vacio
                is_explicit = False
                for p in practicas:
                     if "MARCACION" in normalize_text(p.nombre):
                         is_explicit = True
                         break
                
                if is_explicit:
                     seguimiento.fecha_tac = nuevo_turno.fecha.date()
                     updated = True
                elif not seguimiento.fecha_tac:
                     seguimiento.fecha_tac = nuevo_turno.fecha.date()
                     updated = True

            # 🟢 NEW: Update Sede and Technique if not set (or always?)
            # Let's update technique if we find a specific one
            technique = None
            for p in practicas:
                p_name_upper = p.nombre.upper()
                if "IMRT" in p_name_upper:
                    technique = "IMRT"
                elif "3D" in p_name_upper or "TRIDIMENSIONAL" in p_name_upper:
                    technique = "RT 3D"
            
            if technique and technique != seguimiento.tipo_tecnica:
                seguimiento.tipo_tecnica = technique
                updated = True
                
            # Update Sede if generic/empty
            current_sede = None
            a_name = agenda.nombre.upper()
            if agenda.id == 3 or "SAN MARTIN" in a_name:
                current_sede = "San Martín"
            elif agenda.id == 4 or "COLOMBIA" in a_name:
                current_sede = "Colombia"
            
            if current_sede and not seguimiento.sede:
                 seguimiento.sede = current_sede
                 updated = True

            if updated:
                db.add(seguimiento)
                # db.commit() <-- Removed internal commit

        # ✅ FINAL ATOMIC COMMIT
        # This commit saves BOTH the Turno and any Radiotherapy Tracking changes.
        # If any exception occurred above, we jump to except block and NOTHING is saved.
        db.commit()
        db.refresh(nuevo_turno)

        return nuevo_turno
    except HTTPException as e:
        raise e
    except Exception as e:
        import traceback
        traceback.print_exc()
        # Implicit rollback on exception
        raise HTTPException(status_code=500, detail=f"Error interno creando turno: {str(e)}")


@router.get("/", response_model=List[TurnoOut])
def listar_turnos(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    paciente_id: Optional[int] = Query(default=None),
    agenda_id: Optional[int] = Query(default=None),
    estado: Optional[str] = Query(default=None),
    paciente_dni: Optional[str] = Query(default=None), # Nuevo filtro
    start_date: Optional[str] = Query(default=None), # Nuevo filtro para dashboard (YYYY-MM-DD)
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

    # 🟢 Nuevo filtro por Fecha de Inicio (para Dashboard)
    if start_date is not None:
        # Asegurar que comparamos fecha vs datetime correctamente
        from datetime import datetime, time
        try:
             # Si start_date viene como string "YYYY-MM-DD"
             if isinstance(start_date, str):
                 start_dt = datetime.strptime(start_date, "%Y-%m-%d")
             else:
                 start_dt = datetime.combine(start_date, time.min)
             
             query = query.filter(Turno.fecha >= start_dt)
        except Exception as e:
            print(f"Error filtering by start_date: {e}")

    turnos = query.order_by(Turno.fecha).offset(offset).limit(limit).all()
    return turnos

# 🟢 Eliminar turno
@router.delete("/{turno_id}")
def eliminar_turno(turno_id: int, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    turno = db.get(Turno, turno_id)
    if not turno:
        raise HTTPException(status_code=404, detail="Turno no encontrado")
    
    # 🛡️ SECURTY CHECK: Solo ADMIN puede borrar completados
    if turno.estado == "COMPLETADO" and current_user.get("role") != "ADMIN":
        raise HTTPException(
            status_code=403, 
            detail="⚠️ ACCESO DENEGADO: No tiene permisos para eliminar un turno COMPLETADO. Contacte al administrador."
        )

    # 📝 AUDIT LOG
    try:
        log_msg = f"[AUDIT] TURN DELETED | ID: {turno.id} | USER: {current_user.get('username')} ({current_user.get('role')}) | PACIENTE: {turno.paciente_id} | FECHA: {turno.fecha} | ESTADO_PREVIO: {turno.estado}"
        print(log_msg)
        # Opcional: Escribir a archivo si se desea persistencia simple
        with open("audit_log.txt", "a") as f:
            f.write(f"{datetime.now()} - {log_msg}\n")
    except Exception as e:
        print(f"Error logging audit: {e}")

    db.delete(turno)
    db.commit()
    return {"mensaje": f"Turno {turno_id} eliminado correctamente"}


from schemas.turno import TurnoUpdate

@router.patch("/{turno_id}", response_model=TurnoOut)
def actualizar_turno(turno_id: int, turno_in: TurnoUpdate, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    print(f"RECIBIDO PATCH para turno {turno_id} con datos: {turno_in}")
    turno = db.get(Turno, turno_id)
    if not turno:
        raise HTTPException(status_code=404, detail="Turno no encontrado")
    
    # 🛡️ SECURITY CHECK: Si está COMPLETADO, solo ADMIN puede modificarlo (incluyendo pasarlo a AUSENTE)
    if turno.estado == "COMPLETADO" and current_user.get("role") != "ADMIN":
        raise HTTPException(
            status_code=403, 
            detail="⚠️ ACCESO DENEGADO: No tiene permisos para modificar un turno COMPLETADO."
        )

    # Capture old date for tracking logic
    old_date = turno.fecha.date() if turno.fecha else None

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
            
            # 🟢 VALIDACIÓN DE REGLAS DE NEGOCIO (e.g. Domingos, Horarios, Duplicados)
            from services.turno_service import validate_date_rules, validate_time_rules, validate_duplicate_rules, check_availability
            validate_date_rules(fecha_hora_real)
            validate_time_rules(nueva_hora_str)
            
            # Validar Duplicados (si cambia fecha/hora)
            practicas_ids = [p.id for p in turno.practicas]
            pato_final = turno_in.patologia if turno_in.patologia is not None else turno.patologia
            validate_duplicate_rules(db, turno.paciente_id, turno.agenda_id, fecha_hora_real, practicas_ids, exclude_turno_id=turno.id, patologia=pato_final)

            # 🟢 EXCEPCIÓN RADIOTERAPIA: Verificar disponibilidad con excepción para el mismo paciente
            # Calculamos duración actual (o la nueva si viene en el input)
            duracion_calc = turno_in.duracion if turno_in.duracion is not None else (turno.duracion if turno.duracion else 15)
            try:
                check_availability(db, turno.agenda_id, fecha_hora_real, duracion_calc, turno.agenda.tipo)
            except HTTPException as e:
                # 🟢 EXCEPCIÓN RADIOTERAPIA: Capturamos cualquier error 400
                if e.status_code == 400:
                    from services.turno_service import validate_same_patient_overlap
                    pato_final = turno_in.patologia if turno_in.patologia is not None else turno.patologia
                    try:
                        if validate_same_patient_overlap(db, turno.paciente_id, turno.agenda_id, fecha_hora_real, duracion_calc, turno.practicas, pato_final):
                            pass # Permitir
                        else:
                            raise e
                    except HTTPException as he:
                        raise he
                    except Exception:
                        raise e
                else:
                    raise e

            turno.fecha = fecha_hora_real
            turno.hora = nueva_hora_str
        except HTTPException as he:
            raise he
        except Exception as e:
             print(f"Error actualizando fecha/hora: {e}")
             raise HTTPException(status_code=400, detail="Formato de hora inválido")
    if turno_in.estado is not None:
        turno.estado = turno_in.estado.upper()
    if turno_in.duracion is not None:
        turno.duracion = turno_in.duracion

    # Manejo Médico Derivante (ID o Nombre)
    if turno_in.medico_derivante_id is not None:
        turno.medico_derivante_id = turno_in.medico_derivante_id
    elif turno_in.medico_derivante_nombre:
        # Si viene nombre, buscamos o creamos
        from models.medico import MedicoDerivante
        nombre_medico = turno_in.medico_derivante_nombre.strip().upper()
        medico_existente = db.query(MedicoDerivante).filter(MedicoDerivante.nombre == nombre_medico).first()
        if medico_existente:
            turno.medico_derivante_id = medico_existente.id
        else:
            nuevo_medico = MedicoDerivante(nombre=nombre_medico)
            db.add(nuevo_medico)
            db.commit()
            db.refresh(nuevo_medico)
            turno.medico_derivante_id = nuevo_medico.id

    if turno_in.patologia is not None:
        turno.patologia = turno_in.patologia.strip().upper() if turno_in.patologia else None

    db.commit()
    db.commit()
    db.refresh(turno)

    # 🟢 AUTOMATION: Create Radiotherapy Registry on Trigger (Patch with crear_seguimiento=True)
    if turno_in.crear_seguimiento:
        try:
             # Logic Duplicated from crear_turno (Refactor later into service if possible)
             # 1. Check if already exists (Active)
             from models.radioterapia import SeguimientoRadioterapia
             from sqlalchemy import desc
             from models.medico import MedicoDerivante

             cutoff_date = datetime.now().date() - timedelta(days=60)
             latest_seg = db.query(SeguimientoRadioterapia)\
                 .filter(SeguimientoRadioterapia.paciente_id == turno.paciente_id)\
                 .order_by(desc(SeguimientoRadioterapia.created_at))\
                 .first()

             is_finished = False
             if latest_seg and latest_seg.fecha_fin:
                 if latest_seg.fecha_fin < cutoff_date:
                     is_finished = True
             
             seguimiento = None
             if not latest_seg or (latest_seg and is_finished):
                 # Create NEW
                 # Determine Responsible
                 agenda = turno.agenda
                 practicas = turno.practicas
                 
                 responsable = "Dr. Angel Miño" # Default fallback
                 a_name = agenda.nombre.upper()
                 if "DUARTE" in a_name:
                     responsable = "Dra. Duarte Angelica"
                 elif "MIÑO" in a_name:
                     responsable = "Dr. Angel Miño"
                 
                 # Determine Sede
                 sede = None
                 if agenda.id == 3 or "SAN MARTIN" in a_name:
                     sede = "San Martín"
                 elif agenda.id == 4 or "COLOMBIA" in a_name:
                     sede = "Colombia"
                     
                 # Determine Technique
                 technique = None
                 for p in practicas:
                     p_name_upper = p.nombre.upper()
                     if "IMRT" in p_name_upper:
                         technique = "IMRT"
                     elif "3D" in p_name_upper or "TRIDIMENSIONAL" in p_name_upper:
                         technique = "RT 3D"
                 
                 # Get Derivante Name
                 derivante_name = ""
                 if turno.medico_derivante_id:
                     md = db.get(MedicoDerivante, turno.medico_derivante_id)
                     if md: derivante_name = md.nombre
                 
                 # IMPORTANT: Use Turno Date as Initial Date if not explicitly tracked before
                 seguimiento = SeguimientoRadioterapia(
                     paciente_id=turno.paciente_id,
                     patologia=turno.patologia,
                     medico_derivante=derivante_name,
                     medico_responsable=responsable,
                     sede=sede,
                     tipo_tecnica=technique,
                     fecha_consulta=turno.fecha.date(), # Or today? Usually consult date matches.
                     created_at=datetime.now()
                 )
                 db.add(seguimiento)
                 db.commit()
                 print(f"✅ Seguimiento creado manualmente para turno {turno.id}")
             else:
                 print(f"ℹ️ Seguimiento activo ya existe, no se crea uno nuevo.")

        except Exception as e:
            print(f"Error creating tracking on trigger: {e}")

    # 🟢 AUTOMATION: Update Radiotherapy Registry on Reschedule
    if turno_in.fecha is not None:
        try:
            from models.radioterapia import SeguimientoRadioterapia
            from sqlalchemy import desc
            # Find associated tracking
            # 🟢 AUTOMATION: Check if we need to create a NEW record on UPDATE?
            # Scenario: Patient comes back after 60 days, user reschedules an old appointment? 
            # No, usually reschedule is for active.
            # But if the user edits the appointment to mark "Iniciar Seguimiento", we should check logic.
            # For now, let's keep the existing logic of find_latest.
            
            seguimiento = db.query(SeguimientoRadioterapia)\
                .filter(SeguimientoRadioterapia.paciente_id == turno.paciente_id)\
                .order_by(desc(SeguimientoRadioterapia.created_at))\
                .first()
                
            # Re-apply finished logic if we are "Finding" it?
            # If we are just updating a date, we probably want the latest one, unless it's very old.
            # But assume reschedule is relevant to the *current* or *latest* context.
            
            if seguimiento:
                 updated_track = False
                 agenda = turno.agenda
                 practicas = turno.practicas
                 
                 # Check Agenda Type
                 is_radio_agenda = agenda.tipo == "RADIOTERAPIA" or agenda.id in [3, 4]
                 
                  # Check Practice (TAC de Marcación)
                 is_tac_marcacion = False
                 for p in practicas:
                     # 🟢 FIX: Normalize Accents (Marcación -> MARCACION)
                     import unicodedata
                     def normalize_text(text):
                         return ''.join(c for c in unicodedata.normalize('NFD', text) if unicodedata.category(c) != 'Mn').upper()

                     p_name = normalize_text(p.nombre)
                     if "MARCACION" in p_name:
                         is_tac_marcacion = True
                     if agenda.tipo == "TOMOGRAFIA" and "TAC" in p_name:
                          if not seguimiento.fecha_tac or (old_date and seguimiento.fecha_tac == old_date):
                              is_tac_marcacion = True
                 
                 # Update Dates if applicable
                 new_date = turno.fecha.date()
                 
                 if is_radio_agenda:
                      # Update start date logic (intelligent)
                      # If previous start date was THIS turno's old date, update it.
                      # Or if existing date is None.
                      # Or if new date is earlier.
                      if not seguimiento.fecha_inicio or new_date < seguimiento.fecha_inicio:
                          seguimiento.fecha_inicio = new_date
                          updated_track = True
                 
                 if is_tac_marcacion:
                       # If it explicitly says MARCACION, we trust this new date
                       is_explicit = False
                       for p in practicas:
                           if "MARCACION" in normalize_text(p.nombre):
                               is_explicit = True
                               break
                       
                       if is_explicit:
                           seguimiento.fecha_tac = new_date
                           updated_track = True
                       elif not seguimiento.fecha_tac or (old_date and seguimiento.fecha_tac == old_date):
                           seguimiento.fecha_tac = new_date
                           updated_track = True

                 # 🟢 NEW: Update Technique on Reschedule
                 technique = None
                 for p in practicas:
                      p_name_upper = p.nombre.upper()
                      if "IMRT" in p_name_upper:
                          technique = "IMRT"
                      elif "3D" in p_name_upper or "TRIDIMENSIONAL" in p_name_upper:
                          technique = "RT 3D"
                 
                 if technique and technique != seguimiento.tipo_tecnica:
                     seguimiento.tipo_tecnica = technique
                     updated_track = True

                 if updated_track:
                     db.add(seguimiento)
                     db.commit()
        except Exception as e:
            print(f"Error updating tracking on reschedule: {e}")

    return turno



@router.get("/available_slots")
def get_available_slots(
    agenda_id: int,
    fecha: str, # YYYY-MM-DD
    duracion: int,
    practicas_ids: List[int] = Query(...),
    days_count: int = Query(default=1),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    paciente_id: Optional[int] = Query(default=None)
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

    # Load practices for duration and special overlap rules
    from models.practica import Practica
    practicas = db.query(Practica).filter(Practica.id.in_(practicas_ids)).all()

    # Generate candidate slots (e.g., 8:00 to 20:00)
    # TODO: Make this configurable per agenda or global setting
    start_hour = 7
    end_hour = 24
    interval = 10 # minutes, granularity for search

    available_slots = []
    
    # Generate list of working days to check
    dates_to_check = []
    current_date = start_date
    while len(dates_to_check) < days_count:
        # Skip weekends
        if current_date.weekday() < 6: # 0-5 are Mon-Sat
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
            # Note: We pass practicas and paciente_id to check special Radiotherapy overlap rules
            if not check_availability_boolean(db, agenda_id, dt_check, duracion, agenda.tipo, paciente_id=paciente_id, practicas=practicas):
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
    from sqlalchemy.orm import joinedload
    try:
        start_of_day = datetime.strptime(date, "%Y-%m-%d")
        # En Postgres/SQLAlchemy, para comparar fecha exacta a veces es mejor rango
        # Pero intentaremos filtro simple primero. Si fecha tiene hora, usar >= y <
        
        # Filtrar todos los turnos de ese día
        end_of_day = start_of_day.replace(hour=23, minute=59, second=59)
        
        query = db.query(Turno).options(joinedload(Turno.recordatorio_usuario)).filter(
            Turno.fecha >= start_of_day,
            Turno.fecha <= end_of_day
        )

        # 🟢 Optional: allow filtering by pending status if requested (not used by default yet but useful logic)
        # But for now, user just asked for a better view. The frontend filters by date.
        # Let's keep date filter but maybe we need a new param 'pending_only' later.
        # For now, let's just ensure we return the notification columns so frontend can filter.
        
        turnos = query.order_by(Turno.hora).all()
        
        # Manually map to schema to include the user name, or rely on lazy loading if schema handles it?
        # Since TurnoOut has from_attributes=True, it will try to get attributes from the model.
        # But Turno model doesn't have 'recordatorio_usuario_nombre'.
        # We need to attach it to the objects or return a list of dicts.
        
        results = []
        for t in turnos:
            # Create a dict from the model
            t_dict = t.__dict__.copy()
            
            # Populate the custom field
            user_name = None
            if t.recordatorio_usuario:
               user_name = t.recordatorio_usuario.full_name or t.recordatorio_usuario.username
            
            # Since Pydantic 2/V2, or even v1, we can pass the object if we monkeypatch or use a wrapper.
            # But safer to just add the attribute to the instance if it's not a dict (SQLAlchemy models are objects)
            setattr(t, "recordatorio_usuario_nombre", user_name)
            results.append(t)
        
        return results
        
    except ValueError:
        raise HTTPException(status_code=400, detail="Fecha inválida")
