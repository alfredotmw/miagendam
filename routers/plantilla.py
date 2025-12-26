from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from database import get_db
from models.plantilla import Plantilla
from schemas.plantilla import PlantillaCreate, PlantillaOut
from auth.jwt import get_current_user
from typing import List, Optional

router = APIRouter(
    prefix="/plantillas",
    tags=["Plantillas"]
)

@router.post("/", response_model=PlantillaOut)
def crear_plantilla(
    plantilla: PlantillaCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    nueva = Plantilla(
        titulo=plantilla.titulo,
        contenido=plantilla.contenido,
        servicio=plantilla.servicio,
        creado_por_id=current_user.get("id")
    )
    db.add(nueva)
    db.commit()
    db.refresh(nueva)
    return nueva

@router.get("/", response_model=List[PlantillaOut])
def listar_plantillas(
    servicio: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    query = db.query(Plantilla)
    if servicio:
        # Filter by service OR generic (null service)
        # Or maybe just filter by service if provided. 
        # For simplicity, let's filter by service if provided, or return all.
        query = query.filter(Plantilla.servicio == servicio)
    
    return query.all()

@router.delete("/{id}")
def eliminar_plantilla(
    id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    plantilla = db.query(Plantilla).filter(Plantilla.id == id).first()
    if not plantilla:
        raise HTTPException(status_code=404, detail="Plantilla no encontrada")
    
    db.delete(plantilla)
    db.commit()
    return {"message": "Plantilla eliminada"}
