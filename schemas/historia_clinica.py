from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List, Union

class HistoriaClinicaBase(BaseModel):
    texto: str
    servicio: str

class HistoriaClinicaCreate(HistoriaClinicaBase):
    paciente_id: int
    medico_id: Optional[int] = None

class HistoriaClinicaOut(HistoriaClinicaBase):
    id: int
    paciente_id: int
    fecha: datetime
    medico_id: Optional[int] = None

    class Config:
        orm_mode = True

# Schema for the Unified Timeline
class TimelineEvent(BaseModel):
    tipo: str # "NOTA", "TURNO"
    fecha: datetime
    descripcion: str # "Evolución Dr. X" or "Tomografía de Torax"
    detalle: str # The note text or extra info about the turno (status, etc)
    id_referencia: Optional[int] # ID of the note or the turno
    estado: Optional[str] = None # For turnos: "Asistido", "Ausente", etc.
    servicio: Optional[str] = None

from schemas.paciente import PacienteOut

class TimelineResponse(BaseModel):
    paciente_id: int
    paciente: Optional[PacienteOut] = None
    timeline: List[TimelineEvent]
