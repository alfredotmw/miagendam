from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models.obra_social import ObraSocial
from schemas.obra_social import ObraSocialCreate, ObraSocialUpdate, ObraSocialOut
from typing import List
from auth.jwt import get_current_user

@router.post("/", response_model=ObraSocialOut)
def crear_obra_social(obra: ObraSocialCreate, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    existente = db.query(ObraSocial).filter(ObraSocial.nombre == obra.nombre).first()
    if existente:
        raise HTTPException(status_code=400, detail="Ya existe una obra social con ese nombre")
    nueva_obra = ObraSocial(**obra.dict())
    db.add(nueva_obra)
    db.commit()
    db.refresh(nueva_obra)
    return nueva_obra

@router.get("/", response_model=List[ObraSocialOut])
def listar_obras_sociales(db: Session = Depends(get_db)):
    return db.query(ObraSocial).order_by(ObraSocial.nombre).all()

@router.get("/{obra_id}", response_model=ObraSocialOut)
def obtener_obra_social(obra_id: int, db: Session = Depends(get_db)):
    obra = db.query(ObraSocial).filter(ObraSocial.id == obra_id).first()
    if not obra:
        raise HTTPException(status_code=404, detail="Obra social no encontrada")
    return obra

@router.put("/{obra_id}", response_model=ObraSocialOut)
def actualizar_obra_social(obra_id: int, datos: ObraSocialUpdate, db: Session = Depends(get_db)):
    obra = db.query(ObraSocial).filter(ObraSocial.id == obra_id).first()
    if not obra:
        raise HTTPException(status_code=404, detail="Obra social no encontrada")
    for key, value in datos.dict(exclude_unset=True).items():
        setattr(obra, key, value)
    db.commit()
    db.refresh(obra)
    return obra

@router.delete("/{obra_id}")
def eliminar_obra_social(obra_id: int, db: Session = Depends(get_db)):
    obra = db.query(ObraSocial).filter(ObraSocial.id == obra_id).first()
    if not obra:
        raise HTTPException(status_code=404, detail="Obra social no encontrada")
    db.delete(obra)
    db.commit()
    return {"mensaje": f"Obra social '{obra.nombre}' eliminada correctamente"}

