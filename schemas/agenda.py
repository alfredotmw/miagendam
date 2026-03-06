from pydantic import BaseModel
from typing import Optional, List


class AgendaBase(BaseModel):
    nombre: str
    tipo: str
    slot_minutos: int = 20
    activo: bool = True


class AgendaCreate(AgendaBase):
    pass


class AgendaUpdate(BaseModel):
    nombre: Optional[str] = None
    tipo: Optional[str] = None
    slot_minutos: Optional[int] = None
    activo: Optional[bool] = None
    allowed_user_ids: Optional[List[int]] = None # List of User IDs to permit


class AgendaOut(AgendaBase):
    id: int
    profesional: Optional[str] = None
    allowed_user_ids: List[int] = [] # For output

    class Config:
        from_attributes = True
