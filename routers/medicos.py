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

@router.get("/", response_model=List[MedicoResponse])
def get_medicos(db: Session = Depends(get_db)):
    return db.query(MedicoDerivante).all()

@router.post("/", response_model=MedicoResponse)
def create_medico(medico: MedicoCreate, db: Session = Depends(get_db)):
    db_medico = db.query(MedicoDerivante).filter(MedicoDerivante.nombre == medico.nombre).first()
    if db_medico:
        return db_medico
    
    new_medico = MedicoDerivante(**medico.dict())
    db.add(new_medico)
    db.commit()
    db.refresh(new_medico)
    return new_medico
