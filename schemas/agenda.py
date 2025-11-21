from pydantic import BaseModel
from enum import Enum
from typing import Optional


class AgendaTipo(str, Enum):
    MEDICO = "MEDICO"
    SERVICIO = "SERVICIO"


class AgendaBase(BaseModel):
    nombre: str
    tipo: AgendaTipo
    slot_minutos: int
    activo: bool = True


class AgendaCreate(AgendaBase):
    pass  # 👈 ya no incluimos owner_username manualmente


class AgendaUpdate(BaseModel):
    nombre: Optional[str] = None
    tipo: Optional[AgendaTipo] = None
    slot_minutos: Optional[int] = None
    activo: Optional[bool] = None


class AgendaOut(AgendaBase):
    id: int
    owner_username: str

    class Config:
        from_attributes = True  # reemplaza orm_mode en Pydantic v2
