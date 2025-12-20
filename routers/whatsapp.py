from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models.turno import Turno
from models.paciente import Paciente
from auth.jwt import get_current_user
import urllib.parse

router = APIRouter(
    prefix="/whatsapp",
    tags=["WhatsApp"],
)

@router.get("/link/{turno_id}")
def generar_link_whatsapp(turno_id: int, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    turno = db.query(Turno).filter(Turno.id == turno_id).first()
    if not turno:
        raise HTTPException(status_code=404, detail="Turno no encontrado")
    
    paciente = db.query(Paciente).filter(Paciente.id == turno.paciente_id).first()
    if not paciente:
        raise HTTPException(status_code=404, detail="Paciente no encontrado")
        
    telefono = paciente.celular or paciente.telefono
    if not telefono:
        raise HTTPException(status_code=400, detail="El paciente no tiene número de teléfono registrado")
        
    # Limpiar número (asumiendo formato Argentina, ajustar según necesidad)
    # Si viene con 0 al principio, sacarlo. Si no tiene 54, agregarlo.
    # Esto es una lógica básica, se puede mejorar.
    numero = telefono.strip().replace("+", "").replace(" ", "").replace("-", "")
    if not numero.startswith("54"):
        numero = "54" + numero
        
    fecha_str = turno.fecha.strftime("%d/%m/%Y")
    fecha_str = turno.fecha.strftime("%d/%m/%Y")
    # hora ya es un string en la base de datos (ej: "09:30")
    hora_str = turno.hora
    
    mensaje = f"Hola {paciente.nombre}, le recordamos su turno en Centro Oncológico Corrientes para el día {fecha_str} a las {hora_str}."
    mensaje_encoded = urllib.parse.quote(mensaje)
    
    link = f"https://wa.me/{numero}?text={mensaje_encoded}"
    
    return {"link": link, "mensaje": mensaje, "numero": numero}
