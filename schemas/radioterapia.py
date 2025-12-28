from pydantic import BaseModel
from typing import Optional
from datetime import date, datetime
from schemas.paciente import PacienteOut

class SeguimientoRadioterapiaBase(BaseModel):
    paciente_id: int
    patologia: Optional[str] = None
    medico_derivante: Optional[str] = None
    fecha_consulta: Optional[date] = None
    fecha_tac: Optional[date] = None
    fecha_inicio: Optional[date] = None
    fecha_fin: Optional[date] = None
    medico_responsable: Optional[str] = None
    observaciones: Optional[str] = None

class SeguimientoRadioterapiaCreate(SeguimientoRadioterapiaBase):
    pass

class SeguimientoRadioterapiaUpdate(BaseModel):
    patologia: Optional[str] = None
    medico_derivante: Optional[str] = None
    fecha_consulta: Optional[date] = None
    fecha_tac: Optional[date] = None
    fecha_inicio: Optional[date] = None
    fecha_fin: Optional[date] = None
    medico_responsable: Optional[str] = None
    observaciones: Optional[str] = None

class SeguimientoRadioterapiaOut(SeguimientoRadioterapiaBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    paciente: Optional[PacienteOut] = None

    class Config:
        orm_mode = True
