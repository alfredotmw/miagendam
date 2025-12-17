from pydantic import BaseModel
from typing import Optional

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

    class Config:
        from_attributes = True

