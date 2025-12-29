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
from datetime import date

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
    
    # Check autofills
    for reg in registros:
        check_and_autofill(reg, db)
    
    # Flatten Data
    data = []
    for reg in registros:
        pat = reg.paciente
        data.append({
            "ID": reg.id,
            "Fecha": reg.fecha_consulta,
            "Apellido": pat.apellido if pat else "",
            "Nombre": pat.nombre if pat else "",
            "DNI": pat.dni if pat else "",
            "Patologia": reg.patologia,
            "Dosis": reg.dosis_total,
            "Fracciones": reg.numero_fracciones,
            "Medico_Responsable": reg.medico_responsable,
            "Medico_Derivante": reg.medico_derivante,
            "Fecha_TAC": reg.fecha_tac,
            "Inicio_Tto": reg.fecha_inicio,
            "Fin_Tto": reg.fecha_fin,
            "Estado": ("Finalizado" if reg.fecha_fin and reg.fecha_fin < date.today() else "En Curso") if reg.fecha_inicio else "Pendiente",
            "Observaciones": reg.observaciones
        })
    return data

@router.post("/", response_model=SeguimientoRadioterapiaOut)
def create_registro(
    registro: SeguimientoRadioterapiaCreate, 
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
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
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    query = db.query(SeguimientoRadioterapia)
    if q:
        # Basic filtering logic could be improved (join patient name)
        pass # TODO: Search by patient name if needed
        
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
    """
    changes = False

    # 1. FECHA TAC (Simulacion)
    # Look for latest 'TOMOGRAFIA' appointment
    if not reg.fecha_tac:
        last_tac = db.query(Turno).join(Agenda).join(Practica, Turno.practica_id == Practica.id, isouter=True).filter(
            Turno.paciente_id == reg.paciente_id,
            Turno.estado == "COMPLETADO", # Only completed? Or asignado? User said "a medida que se cargan". So maybe any valid state.
                                          # Let's say "ASISTIO" or just existing event? 
                                          # Usually date is known when turno is taken.
            (Agenda.tipo == "TOMOGRAFIA") | (Practica.categoria == "TOMOGRAFIA")
        ).order_by(Turno.fecha.desc()).first()
        
        if last_tac:
            reg.fecha_tac = last_tac.fecha.date()
            changes = True

    # 2. FECHA INICIO TTO (First Radiotherapy Session)
    if not reg.fecha_inicio:
        first_radio = db.query(Turno).join(Agenda).filter(
            Turno.paciente_id == reg.paciente_id,
            Agenda.tipo == "RADIOTERAPIA"
        ).order_by(Turno.fecha.asc()).first()
        
        if first_radio:
            reg.fecha_inicio = first_radio.fecha.date()
            changes = True

    # 3. FECHA FIN TTO (Last Radiotherapy Session)
    # We always update 'fin' if we find a later date than current 'fin' or if 'fin' is missing
    last_radio = db.query(Turno).join(Agenda).filter(
        Turno.paciente_id == reg.paciente_id,
        Agenda.tipo == "RADIOTERAPIA"
    ).order_by(Turno.fecha.desc()).first()

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
