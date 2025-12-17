from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import date
from schemas.obra_social import ObraSocialOut  # 👈 Importamos para mostrar el nombre en la respuesta

class PacienteBase(BaseModel):
    nombre: str
    apellido: str
    dni: str
    fecha_nacimiento: Optional[date] = None
    sexo: Optional[str] = None
    telefono: Optional[str] = None
    celular: Optional[str] = None
    email: Optional[EmailStr] = None
    direccion: Optional[str] = None
    obra_social_id: Optional[int] = None  # se elige desde el combo

class PacienteCreate(PacienteBase):
    obra_social_nombre: Optional[str] = None

class PacienteUpdate(PacienteBase):
    obra_social_nombre: Optional[str] = None

class PacienteOut(PacienteBase):
    id: int
    edad: Optional[int] = None # Campo calculado
    obra_social: Optional[ObraSocialOut] = None  # 👈 devuelve datos de la obra social

    class Config:
        from_attributes = True


