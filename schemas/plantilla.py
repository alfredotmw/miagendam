from pydantic import BaseModel
from typing import Optional

class PlantillaBase(BaseModel):
    titulo: str
    contenido: str
    servicio: Optional[str] = None

class PlantillaCreate(PlantillaBase):
    pass

class PlantillaOut(PlantillaBase):
    id: int
    creado_por_id: Optional[int] = None

    class Config:
        orm_mode = True
