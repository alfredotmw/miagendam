from fastapi import APIRouter, Depends
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from models.agenda import Agenda
from auth.jwt import get_current_user

router = APIRouter(prefix="/agendas", tags=["Agendas"])

@router.get("/")
def listar_agendas(db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    agendas = db.query(Agenda).all()
    return agendas
