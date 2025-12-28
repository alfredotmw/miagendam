from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from database import get_db
from models.radioterapia import SeguimientoRadioterapia
from schemas.radioterapia import SeguimientoRadioterapiaCreate, SeguimientoRadioterapiaOut, SeguimientoRadioterapiaUpdate
from auth.jwt import get_current_user

router = APIRouter(
    prefix="/radioterapia",
    tags=["Radioterapia"]
)

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
        
    return query.order_by(SeguimientoRadioterapia.id.desc()).offset(skip).limit(limit).all()

@router.get("/paciente/{paciente_id}", response_model=List[SeguimientoRadioterapiaOut])
def get_by_patient(
    paciente_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    return db.query(SeguimientoRadioterapia).filter(SeguimientoRadioterapia.paciente_id == paciente_id).all()

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
