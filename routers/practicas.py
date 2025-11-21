from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from models.practica import Practica
from schemas.practica import PracticaCreate, PracticaUpdate, PracticaOut

router = APIRouter(
    prefix="/practicas",
    tags=["Practicas"],
)


@router.get("/", response_model=List[PracticaOut])
def listar_practicas(
    q: Optional[str] = None,
    categoria: Optional[str] = None,
    db: Session = Depends(get_db),
):
    query = db.query(Practica)

    if q:
        like = f"%{q}%"
        query = query.filter(Practica.nombre.ilike(like))

    if categoria:
        query = query.filter(Practica.categoria == categoria)

    return query.order_by(Practica.categoria, Practica.nombre).all()


from auth.jwt import get_current_user

@router.post("/", response_model=PracticaOut, status_code=status.HTTP_201_CREATED)
def crear_practica(data: PracticaCreate, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    existente = db.query(Practica).filter(Practica.nombre == data.nombre).first()
    if existente:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ya existe una práctica con ese nombre",
        )

    practica = Practica(
        nombre=data.nombre,
        categoria=data.categoria,
    )
    db.add(practica)
    db.commit()
    db.refresh(practica)
    return practica
@router.put("/{practica_id}", response_model=PracticaOut)
def actualizar_practica(
    practica_id: int,
    data: PracticaUpdate,
    db: Session = Depends(get_db),
):
    practica = db.query(Practica).get(practica_id)
    if not practica:
        raise HTTPException(status_code=404, detail="Práctica no encontrada")

    if data.nombre is not None:
        practica.nombre = data.nombre
    if data.categoria is not None:
        practica.categoria = data.categoria

    db.commit()
    db.refresh(practica)
    return practica


@router.delete("/{practica_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_practica(practica_id: int, db: Session = Depends(get_db)):
    practica = db.query(Practica).get(practica_id)
    if not practica:
        raise HTTPException(status_code=404, detail="Práctica no encontrada")

    db.delete(practica)
    db.commit()
    return
