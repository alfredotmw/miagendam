from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from models.patologia import Patologia
from auth.jwt import get_current_user

router = APIRouter(
    prefix="/common",
    tags=["Common"]
)

@router.get("/patologias")
def get_patologias(db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    return [p.nombre for p in db.query(Patologia).order_by(Patologia.nombre).all()]
