from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel
from database import get_db
from database import get_db
from models.medico import MedicoDerivante

router = APIRouter(
    prefix="/medicos",
    tags=["medicos"]
)

class MedicoBase(BaseModel):
    nombre: str
    matricula: str | None = None
    telefono: str | None = None

class MedicoCreate(MedicoBase):
    pass

class MedicoResponse(MedicoBase):
    id: int

    class Config:
        from_attributes = True

from auth.jwt import get_current_user

@router.get("/", response_model=List[MedicoResponse])
def get_medicos(db: Session = Depends(get_db)):
    return db.query(MedicoDerivante).all()

@router.post("/", response_model=MedicoResponse)
def create_medico(medico: MedicoCreate, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    db_medico = db.query(MedicoDerivante).filter(MedicoDerivante.nombre == medico.nombre).first()
    if db_medico:
        return db_medico
    
    new_medico = MedicoDerivante(**medico.dict())
    new_medico.creado_por_id = current_user.get("id") # 🛡️ Auditoría
    db.add(new_medico)
    db.commit()
    db.refresh(new_medico)
    return new_medico

@router.put("/{medico_id}", response_model=MedicoResponse)
def update_medico(medico_id: int, medico_in: MedicoCreate, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    db_medico = db.get(MedicoDerivante, medico_id)
    if not db_medico:
        raise HTTPException(status_code=404, detail="Médico no encontrado")
    
    for key, value in medico_in.dict(exclude_unset=True).items():
        setattr(db_medico, key, value)
    
    # 🛡️ Auditoría
    db_medico.modificado_por_id = current_user.get("id")
    
    db.commit()
    db.refresh(db_medico)
    return db_medico
