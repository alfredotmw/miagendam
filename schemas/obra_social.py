from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class ObraSocialBase(BaseModel):
    nombre: str
    codigo: Optional[str] = None
    descripcion: Optional[str] = None

class ObraSocialCreate(ObraSocialBase):
    pass

class ObraSocialUpdate(ObraSocialBase):
    pass

class ObraSocialOut(ObraSocialBase):
    id: int

    # Auditoría
    creado_por_id: Optional[int] = None
    fecha_creacion: Optional[datetime] = None
    modificado_por_id: Optional[int] = None
    fecha_modificacion: Optional[datetime] = None

    class Config:
        from_attributes = True

