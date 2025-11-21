from pydantic import BaseModel
from typing import Optional


class PracticaBase(BaseModel):
    nombre: str
    categoria: str  # TOMOGRAFIA, RADIOGRAFIA, ECOGRAFIA, PET, ELECTRO_MAPEO, RADIOTERAPIA, CAMARA_GAMMA, CONSULTA


class PracticaCreate(PracticaBase):
    pass


class PracticaUpdate(BaseModel):
    nombre: Optional[str] = None
    categoria: Optional[str] = None


class PracticaOut(PracticaBase):
    id: int

    class Config:
        from_attributes = True
