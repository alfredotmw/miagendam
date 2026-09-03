# routers/informe_clinico.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
from models.informe_clinico import InformeClinico
from models.turno import Turno
from schemas.informe_clinico import (
    InformeClinicoCreate,
    InformeClinicoUpdate,
    InformeClinicoFinalize,
    InformeClinicoOut,
    InformeClinicoReceptionOut,
    validate_content_json
)
from auth.jwt import get_current_user
from datetime import datetime, timezone
import json

router = APIRouter(
    prefix="",
    tags=["Informes Clinicos"]
)

# Feature Flag validation dependency
def check_feature_flag():
    import config
    # Ensure it behaves exactly as disabled if flag is False
    if not getattr(config, "ENABLE_CLINICAL_REPORTS", False):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Módulo de informes clínicos no habilitado"
        )

# Helper to verify agenda permission for MEDICO role
def verify_agenda_permission(turno_agenda_id: int, current_user: dict):
    if current_user["role"] == "ADMIN":
        return
        
    if current_user["role"] == "MEDICO":
        allowed_str = current_user.get("allowed_agendas") or ""
        allowed_ids = [int(x.strip()) for x in allowed_str.split(",") if x.strip()]
        # If restricted, check if current agenda is allowed
        if allowed_ids and turno_agenda_id not in allowed_ids:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Acceso denegado: agenda no autorizada para el profesional."
            )
        return
        
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Acceso denegado: rol insuficiente."
    )

# Helper to automatically determine report template type
def determine_report_type(turno) -> str:
    practice_names = []
    if turno.practica:
        practice_names.append(turno.practica.nombre.upper())
    if getattr(turno, "practicas", None):
        practice_names.extend([p.nombre.upper() for p in turno.practicas])
        
    agenda_name = turno.agenda.nombre.upper() if turno.agenda else ""
    
    # Check for ELECTROENCEFALOGRAMA
    if any("ELECTRO" in name for name in practice_names) or "ELECTRO" in agenda_name:
        return "ELECTROENCEFALOGRAMA"
        
    # Check for IMAGENES
    imaging_keywords = ["TOMO", "ECO", "RADIO", "RX", "PET", "MAMA", "TORAX", "CEREBRO", "IMAG", "BIOPSIA", "PUNCION"]
    if any(any(kw in name for kw in imaging_keywords) for name in practice_names) or any(kw in agenda_name for kw in imaging_keywords):
        return "IMAGENES"
        
    # Check for CONSULTA
    if any("CONSULTA" in name for name in practice_names) or "CONSULTA" in agenda_name or "CONSULTORIO" in agenda_name:
        return "CONSULTA_MEDICA"
        
    return "TEXTO_LIBRE"

# Helper to generate consolidated plain text in the backend
def generate_consolidated_text(tipo_informe: str, contenido_json: dict) -> str:
    if tipo_informe == "IMAGENES":
        return (
            "ESTUDIO DE DIAGNÓSTICO POR IMÁGENES\n\n"
            f"Indicación clínica: {contenido_json.get('indicacion_clinica', '')}\n"
            f"Técnica: {contenido_json.get('tecnica', '')}\n"
            f"Hallazgos: {contenido_json.get('hallazgos', '')}\n"
            f"Conclusión: {contenido_json.get('conclusion', '')}\n"
            f"Observaciones: {contenido_json.get('observaciones', '')}"
        )
    elif tipo_informe == "ELECTROENCEFALOGRAMA":
        return (
            "INFORME DE ELECTROENCEFALOGRAMA\n\n"
            f"Indicación clínica: {contenido_json.get('indicacion_clinica', '')}\n"
            f"Técnica: {contenido_json.get('tecnica', '')}\n"
            f"Actividad de fondo: {contenido_json.get('actividad_de_fondo', '')}\n"
            f"Hallazgos: {contenido_json.get('hallazgos', '')}\n"
            f"Maniobras de activación: {contenido_json.get('maniobras_de_activacion', '')}\n"
            f"Conclusión: {contenido_json.get('conclusion', '')}\n"
            f"Observaciones: {contenido_json.get('observaciones', '')}"
        )
    elif tipo_informe == "CONSULTA_MEDICA":
        return (
            "INFORME DE CONSULTA MÉDICA\n\n"
            f"Motivo de consulta: {contenido_json.get('motivo_consulta', '')}\n"
            f"Antecedentes relevantes: {contenido_json.get('antecedentes_relevantes', '')}\n"
            f"Evaluación: {contenido_json.get('evaluacion', '')}\n"
            f"Impresión diagnóstica: {contenido_json.get('impresion_diagnostica', '')}\n"
            f"Conducta: {contenido_json.get('conducta', '')}\n"
            f"Indicaciones: {contenido_json.get('indicaciones', '')}\n"
            f"Observaciones: {contenido_json.get('observaciones', '')}"
        )
    elif tipo_informe == "TEXTO_LIBRE":
        return (
            "INFORME MÉDICO\n\n"
            f"{contenido_json.get('informe', '')}"
        )
    return ""

@router.get("/turnos/{turno_id}/informe", dependencies=[Depends(check_feature_flag)])
def get_turno_informe(
    turno_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    # 1. Fetch Turno to verify existence and agenda
    turno = db.query(Turno).filter(Turno.id == turno_id).first()
    if not turno:
        raise HTTPException(status_code=404, detail="Turno no encontrado")
        
    # 2. Check agenda permission (not applicable for RECEPCION for status read, but RECEPCION has administrative role rules)
    # RECEPCION can see status, but cannot see content.
    is_recepcion = (current_user["role"] == "RECEPCION")
    
    if not is_recepcion:
        verify_agenda_permission(turno.agenda_id, current_user)
        
    # 3. Query report
    report = db.query(InformeClinico).filter(InformeClinico.turno_id == turno_id).first()
    if not report:
        return None
        
    # 4. Filter response payload based on role
    if is_recepcion:
        return InformeClinicoReceptionOut.from_orm(report)
        
    return InformeClinicoOut.from_orm(report)

@router.post("/turnos/{turno_id}/informe", status_code=201, response_model=InformeClinicoOut, dependencies=[Depends(check_feature_flag)])
def create_turno_informe(
    turno_id: int,
    payload: InformeClinicoCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    # 1. Access validation (RECEPCION cannot create)
    if current_user["role"] == "RECEPCION":
        raise HTTPException(status_code=403, detail="Acceso denegado: rol de recepción no puede crear informes.")
        
    # 2. Fetch Turno
    turno = db.query(Turno).filter(Turno.id == turno_id).first()
    if not turno:
        raise HTTPException(status_code=404, detail="Turno no encontrado")
        
    # 3. Check agenda permission
    verify_agenda_permission(turno.agenda_id, current_user)
        
    # 4. Check for duplicates
    existing = db.query(InformeClinico).filter(InformeClinico.turno_id == turno_id).first()
    if existing:
        raise HTTPException(status_code=409, detail="El turno ya posee un informe clínico asociado.")
        
    # 5. Determine type of report (automatic selection check)
    determined_type = determine_report_type(turno)
    if payload.tipo_informe != determined_type:
        raise HTTPException(
            status_code=400,
            detail=f"Tipo de informe incorrecto para esta agenda/práctica. Determinado: {determined_type}"
        )
        
    # 6. Validate content JSON strictly
    try:
        validated_json = validate_content_json(payload.tipo_informe, payload.contenido_json)
    except ValueError as val_err:
        raise HTTPException(status_code=422, detail=str(val_err))
        
    # Limit payload size roughly (max 100 KB)
    payload_str = json.dumps(payload.contenido_json)
    if len(payload_str.encode('utf-8')) > 102400:
        raise HTTPException(status_code=422, detail="El tamaño del contenido excede el límite permitido (100 KB).")
        
    # 7. Generate plain text
    texto_generado = generate_consolidated_text(payload.tipo_informe, validated_json)
    
    # 8. Create new record
    utc_now = datetime.now(timezone.utc)
    new_report = InformeClinico(
        turno_id=turno_id,
        paciente_id=turno.paciente_id, # Obtained from turno, never from frontend
        tipo_informe=payload.tipo_informe,
        contenido_json=validated_json,
        contenido_texto=texto_generado,
        estado="BORRADOR",
        version=1,
        created_at=utc_now,
        updated_at=utc_now,
        created_by=current_user["id"],
        updated_by=current_user["id"]
    )
    
    db.add(new_report)
    db.commit()
    db.refresh(new_report)
    
    return new_report

@router.put("/informes-clinicos/{informe_id}", response_model=InformeClinicoOut, dependencies=[Depends(check_feature_flag)])
def update_informe(
    informe_id: int,
    payload: InformeClinicoUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    if current_user["role"] == "RECEPCION":
        raise HTTPException(status_code=403, detail="Acceso denegado: rol de recepción no puede modificar informes.")
        
    # 1. Fetch existing report and associated turno
    report = db.query(InformeClinico).filter(InformeClinico.id == informe_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Informe clínico no encontrado")
        
    # 2. Check agenda permission
    turno = db.query(Turno).filter(Turno.id == report.turno_id).first()
    if not turno:
        raise HTTPException(status_code=404, detail="Turno asociado no encontrado")
    verify_agenda_permission(turno.agenda_id, current_user)
    
    # 3. Verify it is still in BORRADOR state
    if report.estado != "BORRADOR":
        raise HTTPException(status_code=409, detail="No se puede modificar un informe ya finalizado o anulado.")
        
    # 4. Strict template json validation
    try:
        validated_json = validate_content_json(report.tipo_informe, payload.contenido_json)
    except ValueError as val_err:
        raise HTTPException(status_code=422, detail=str(val_err))
        
    # Limit payload size roughly
    payload_str = json.dumps(payload.contenido_json)
    if len(payload_str.encode('utf-8')) > 102400:
        raise HTTPException(status_code=422, detail="El tamaño del contenido excede el límite permitido (100 KB).")
        
    # 5. Generate plain text
    texto_generado = generate_consolidated_text(report.tipo_informe, validated_json)
    
    # 6. Execute atomic update (verifying version and status in DB)
    utc_now = datetime.now(timezone.utc)
    updated = db.query(InformeClinico).filter(
        InformeClinico.id == informe_id,
        InformeClinico.version == payload.version,
        InformeClinico.estado == "BORRADOR"
    ).update({
        "contenido_json": validated_json,
        "contenido_texto": texto_generado,
        "version": InformeClinico.version + 1,
        "updated_by": current_user["id"],
        "updated_at": utc_now
    }, synchronize_session=False)
    
    if updated == 0:
        db.rollback()
        # Verify if it failed due to wrong version or changed state
        current_report = db.query(InformeClinico).filter(InformeClinico.id == informe_id).first()
        if current_report.estado != "BORRADOR":
            raise HTTPException(status_code=409, detail="El estado del informe cambió y ya no se puede editar.")
        raise HTTPException(status_code=409, detail="Conflicto de concurrencia: el informe fue modificado por otra sesión.")
        
    db.commit()
    db.refresh(report)
    return report

@router.post("/informes-clinicos/{informe_id}/finalizar", response_model=InformeClinicoOut, dependencies=[Depends(check_feature_flag)])
def finalize_informe(
    informe_id: int,
    payload: InformeClinicoFinalize,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    if current_user["role"] == "RECEPCION":
        raise HTTPException(status_code=403, detail="Acceso denegado: rol de recepción no puede finalizar informes.")
        
    # 1. Fetch existing report and associated turno
    report = db.query(InformeClinico).filter(InformeClinico.id == informe_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Informe clínico no encontrado")
        
    # 2. Check agenda permission
    turno = db.query(Turno).filter(Turno.id == report.turno_id).first()
    if not turno:
        raise HTTPException(status_code=404, detail="Turno asociado no encontrado")
    verify_agenda_permission(turno.agenda_id, current_user)
    
    # 3. Verify it is still in BORRADOR state (or return idempotently if already FINALIZADO)
    if report.estado == "FINALIZADO":
        return report
    if report.estado != "BORRADOR":
        raise HTTPException(status_code=409, detail="El informe ya se encuentra en un estado no editable.")
        
    # 4. Check minimum content validation (at least one field should be filled with non-empty content)
    non_empty = False
    for k, v in report.contenido_json.items():
        if v and str(v).strip():
            non_empty = True
            break
    if not non_empty:
        raise HTTPException(status_code=422, detail="No se puede finalizar un informe clínico vacío.")
        
    # 5. Execute atomic finalization
    utc_now = datetime.now(timezone.utc)
    updated = db.query(InformeClinico).filter(
        InformeClinico.id == informe_id,
        InformeClinico.version == payload.version,
        InformeClinico.estado == "BORRADOR"
    ).update({
        "estado": "FINALIZADO",
        "finalized_by": current_user["id"],
        "finalized_at": utc_now,
        "version": InformeClinico.version + 1,
        "updated_by": current_user["id"],
        "updated_at": utc_now
    }, synchronize_session=False)
    
    if updated == 0:
        db.rollback()
        current_report = db.query(InformeClinico).filter(InformeClinico.id == informe_id).first()
        if current_report.estado == "FINALIZADO":
            # Idempotent response if it was already finalized in a duplicate request
            # Return current state without duplicating finalized_at
            return current_report
        raise HTTPException(status_code=409, detail="Conflicto de concurrencia: el informe fue modificado o finalizado por otra sesión.")
        
    db.commit()
    db.refresh(report)
    return report

@router.get("/informes-clinicos/{informe_id}", response_model=InformeClinicoOut, dependencies=[Depends(check_feature_flag)])
def get_informe_detail(
    informe_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    # 1. Rol RECEPCION gets 403 Forbidden
    if current_user["role"] == "RECEPCION":
        raise HTTPException(status_code=403, detail="Acceso denegado: rol de recepción no puede ver contenido clínico.")
        
    # 2. Fetch Report
    report = db.query(InformeClinico).filter(InformeClinico.id == informe_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Informe clínico no encontrado")
        
    # 3. Validate agenda permission
    turno = db.query(Turno).filter(Turno.id == report.turno_id).first()
    if not turno:
        raise HTTPException(status_code=404, detail="Turno asociado no encontrado")
    verify_agenda_permission(turno.agenda_id, current_user)
    
    return report
