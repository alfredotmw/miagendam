from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from database import get_db
from models.radioterapia import SeguimientoRadioterapia
from schemas.radioterapia import SeguimientoRadioterapiaCreate, SeguimientoRadioterapiaOut, SeguimientoRadioterapiaUpdate
from auth.jwt import get_current_user
from models.turno import Turno
from models.agenda import Agenda
from models.practica import Practica
from datetime import date, datetime

router = APIRouter(
    prefix="/radioterapia",
    tags=["Radioterapia"]
)

from fastapi import Query
from jose import jwt, JWTError
from auth.jwt import SECRET_KEY, ALGORITHM

@router.get("/feed")
def get_excel_feed(
    token: str = Query(..., description="JWT Token for authentication"),
    db: Session = Depends(get_db)
):
    # Verify Token manually
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if "sub" not in payload:
            raise HTTPException(status_code=401, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    registros = db.query(SeguimientoRadioterapia).order_by(SeguimientoRadioterapia.id.desc()).all()
    
    # Check autofills with error handling
    for reg in registros:
        try:
            check_and_autofill(reg, db)
        except Exception as e:
            print(f"Error autofilling reg {reg.id}: {e}")
    
    # Flatten Data
    data = []
    for reg in registros:
        pat = reg.paciente
        data.append({
            # Column 0: ID (Required by Excel cache sometimes)
            "ID": reg.id,
            # Column 1: Nombre y Apellido
            "Paciente": f"{pat.apellido}, {pat.nombre}" if pat else "",
            # Column 2: Edad
            "Edad": pat.edad if pat else "",
            # Column 2.5: Obra Social
            "Obra_Social": pat.obra_social.nombre if pat and pat.obra_social else (pat.nro_afiliado if pat.nro_afiliado else ""),
            # Column 3: Patología
            "Patologia": reg.patologia,
            # Column 4: Medico Responsable
            "Medico_Responsable": reg.medico_responsable,
            # Column 5: Medico Derivante
            "Medico_Derivante": reg.medico_derivante,
            # Column 6: Fecha de Consulta
            "Fecha_Consulta": reg.fecha_consulta,
            # Column 7: Fecha de TAC
            "Fecha_TAC": reg.fecha_tac,
            # Column 8: Inicio Tratamiento
            "Inicio_Tto": reg.fecha_inicio,
            # Column 9: Fin Tratamiento
            "Fin_Tto": reg.fecha_fin,
            # New Columns
            "Sede": reg.sede,
            "Tecnica": reg.tipo_tecnica,
            # Extras (optional, keep at end)
            "Observaciones": reg.observaciones,
            "Estado": ("Finalizado" if reg.fecha_fin and reg.fecha_fin < date.today() else "En Curso") if reg.fecha_inicio else "Pendiente"
        })
    return data

@router.post("/", response_model=SeguimientoRadioterapiaOut)
def create_registro(
    registro: SeguimientoRadioterapiaCreate, 
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    
    # 🟢 SYNC MEDICO DERIVANTE
    if registro.medico_derivante:
        normalized = registro.medico_derivante.strip().upper()
        registro.medico_derivante = normalized
        
        from models.medico import MedicoDerivante
        existing_med = db.query(MedicoDerivante).filter(MedicoDerivante.nombre == normalized).first()
        if not existing_med:
            try:
                db.add(MedicoDerivante(nombre=normalized))
                db.commit()
            except Exception as e:
                print(f"Error Auto-adding medico: {e}")
                db.rollback()

    new_reg = SeguimientoRadioterapia(**registro.dict())
    db.add(new_reg)
    db.commit()
    db.refresh(new_reg)
    return new_reg

@router.get("/", response_model=List[SeguimientoRadioterapiaOut])
def list_registros(
    skip: int = 0, 
    limit: int = 100, 
    q: Optional[str] = None,
    sede: Optional[str] = None,
    estado: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    query = db.query(SeguimientoRadioterapia)
    
    # FILTER: Sede
    if sede:
        if sede == "SIN_ASIGNAR":
             query = query.filter((SeguimientoRadioterapia.sede == None) | (SeguimientoRadioterapia.sede == ""))
        else:
             query = query.filter(SeguimientoRadioterapia.sede == sede)

    # FILTER: Estado
    # Logic:
    # "pendiente": fecha_inicio IS NULL
    # "en_curso": fecha_inicio IS NOT NULL AND (fecha_fin IS NULL OR fecha_fin >= today)
    # "finalizado": fecha_fin < today
    if estado:
        today = date.today()
        if estado == "pendiente":
            query = query.filter(SeguimientoRadioterapia.fecha_inicio == None)
        elif estado == "en_curso":
            query = query.filter(
                SeguimientoRadioterapia.fecha_inicio != None,
                (SeguimientoRadioterapia.fecha_fin == None) | (SeguimientoRadioterapia.fecha_fin >= today)
            )
        elif estado == "finalizado":
             query = query.filter(SeguimientoRadioterapia.fecha_fin < today)

    if q:
        # Basic filtering logic could be improved (join patient name)
        # For now, let's allow basic text search on patologia or patient name if connected
        # But user requested structural filters mainly.
        pass 
        
    registros = query.order_by(SeguimientoRadioterapia.id.desc()).offset(skip).limit(limit).all()
    
    # 🟢 AUTO-FILL LOGIC
    for reg in registros:
        check_and_autofill(reg, db)
        
    return registros

@router.get("/paciente/{paciente_id}", response_model=List[SeguimientoRadioterapiaOut])
def get_by_patient(
    paciente_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    registros = db.query(SeguimientoRadioterapia).filter(SeguimientoRadioterapia.paciente_id == paciente_id).all()
    
    # 🟢 AUTO-FILL LOGIC
    for reg in registros:
        check_and_autofill(reg, db)

    return registros  

def check_and_autofill(reg: SeguimientoRadioterapia, db: Session):
    """
    Checks if dates are missing and tries to fill them from Turnos.
    Updates DB if changes found.
    Respects cycle boundaries to support multiple treatments per patient.
    """
    changes = False

    # 1. Determinar Límites (Boundaries) del Ciclo
    # Start Bound: Fecha de consulta o Fecha de creación del registro
    start_bound = None
    if reg.fecha_consulta:
        start_bound = datetime.combine(reg.fecha_consulta, datetime.min.time())
    else:
        # Intenta buscar una consulta de 1ra vez (Dr. Miño o Dra. Duarte) automáticamente
        query_consulta = db.query(Turno).join(Agenda).filter(
            Turno.paciente_id == reg.paciente_id,
            Turno.estado != "cancelado",
            Agenda.nombre.in_(["CONSULTORIO DR. ANGEL MIÑO", "DRA. MARÍA ANGELICA DUARTE"]) # Adjust names based on actual DB
        ).order_by(Turno.fecha.asc())
        
        # If we have created_at, we can limit to around that time, or we just take the first one before created_at
        first_consulta = query_consulta.first()
        if first_consulta:
            reg.fecha_consulta = first_consulta.fecha.date()
            start_bound = datetime.combine(first_consulta.fecha.date(), datetime.min.time())
            changes = True
        else:
            # Fallback to created_at
            start_bound = reg.created_at

    # End Bound: El inicio del siguiente registro de radioterapia para este paciente (si existe)
    end_bound = None
    if start_bound:
        next_reg = db.query(SeguimientoRadioterapia).filter(
            SeguimientoRadioterapia.paciente_id == reg.paciente_id,
            SeguimientoRadioterapia.id != reg.id,
            SeguimientoRadioterapia.created_at > start_bound
        ).order_by(SeguimientoRadioterapia.created_at.asc()).first()
        
        if next_reg:
            # Boundary is the consultation date or creation date of the next cycle
            if next_reg.fecha_consulta:
                end_bound = datetime.combine(next_reg.fecha_consulta, datetime.min.time())
            else:
                end_bound = next_reg.created_at

    # Helper function to apply boundaries
    def apply_bounds(query, date_column):
        if start_bound:
            query = query.filter(date_column >= start_bound)
        if end_bound:
            query = query.filter(date_column < end_bound)
        return query

    # 2. FECHA TAC (Simulacion)
    if not reg.fecha_tac:
        query_tac = db.query(Turno).join(Agenda).join(Practica, Turno.practica_id == Practica.id, isouter=True).filter(
            Turno.paciente_id == reg.paciente_id,
            Turno.estado != "cancelado", # Exclude canceled
            (Agenda.tipo == "TOMOGRAFIA") | (Practica.categoria == "TOMOGRAFIA")
        )
        query_tac = apply_bounds(query_tac, Turno.fecha)
        # Assuming the first TAC in the cycle is the relevant one
        first_tac = query_tac.order_by(Turno.fecha.asc()).first()
        
        if first_tac:
            reg.fecha_tac = first_tac.fecha.date()
            changes = True

    # 3. FECHA INICIO TTO (First Radiotherapy Session in this cycle)
    if not reg.fecha_inicio:
        query_inicio = db.query(Turno).join(Agenda).filter(
            Turno.paciente_id == reg.paciente_id,
            Turno.estado != "cancelado",
            Agenda.tipo == "RADIOTERAPIA"
        )
        query_inicio = apply_bounds(query_inicio, Turno.fecha)
        first_radio = query_inicio.order_by(Turno.fecha.asc()).first()
        
        if first_radio:
            reg.fecha_inicio = first_radio.fecha.date()
            changes = True

    # 4. FECHA FIN TTO (Last Radiotherapy Session in this cycle)
    query_fin = db.query(Turno).join(Agenda).filter(
        Turno.paciente_id == reg.paciente_id,
        Turno.estado != "cancelado",
        Agenda.tipo == "RADIOTERAPIA"
    )
    query_fin = apply_bounds(query_fin, Turno.fecha)
    last_radio = query_fin.order_by(Turno.fecha.desc()).first()

    if last_radio:
        last_date = last_radio.fecha.date()
        if not reg.fecha_fin or reg.fecha_fin != last_date:
            reg.fecha_fin = last_date
            changes = True

    if changes:
        db.add(reg)
        db.commit()
        db.refresh(reg)

@router.put("/{reg_id}", response_model=SeguimientoRadioterapiaOut)
def update_registro(
    reg_id: int, 
    registro_update: SeguimientoRadioterapiaUpdate, 
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    db_reg = db.query(SeguimientoRadioterapia).get(reg_id)
    if not db_reg:
        raise HTTPException(status_code=404, detail="Registro no encontrado")
    
    for key, value in registro_update.dict(exclude_unset=True).items():
        if key == "medico_derivante" and value:
            # 🟢 SYNC MEDICO DERIVANTE UPDATE
            normalized = value.strip().upper()
            setattr(db_reg, key, normalized)
            
            from models.medico import MedicoDerivante
            existing_med = db.query(MedicoDerivante).filter(MedicoDerivante.nombre == normalized).first()
            if not existing_med:
                try:
                    db.add(MedicoDerivante(nombre=normalized))
                    db.commit()
                except Exception as e:
                    print(f"Error Auto-adding medico update: {e}")
                    db.rollback()
        else:
            setattr(db_reg, key, value)
    
    db.commit()
    db.refresh(db_reg)
    return db_reg

@router.delete("/{reg_id}")
def delete_registro(
    reg_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    db_reg = db.query(SeguimientoRadioterapia).get(reg_id)
    if not db_reg:
        raise HTTPException(status_code=404, detail="Registro no encontrado")
    
    db.delete(db_reg)
    db.commit()
    return {"ok": True}
