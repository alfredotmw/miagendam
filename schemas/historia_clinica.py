from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List, Union

class HistoriaClinicaBase(BaseModel):
    texto: Optional[str] = None
    servicio: str
    motivo_consulta: Optional[str] = None
    antecedentes: Optional[str] = None
    examen_clinico: Optional[str] = None
    plan_estudio: Optional[str] = None
    diagnostico_diferencial: Optional[str] = None
    tratamiento: Optional[str] = None
    evolucion: Optional[str] = None
    estado: Optional[str] = "BORRADOR"
    # P1 Oncology
    ecog: Optional[int] = None # 0-5
    tnm: Optional[str] = None
    estadio: Optional[str] = None
    toxicidad: Optional[str] = None

class HistoriaClinicaCreate(HistoriaClinicaBase):
    paciente_id: int
    medico_id: Optional[int] = None
    accion: Optional[str] = "GUARDAR" # GUARDAR | FIRMAR

class HistoriaClinicaOut(HistoriaClinicaBase):
    id: int
    paciente_id: int
    fecha: datetime
    medico_id: Optional[int] = None
    
    creado_por_id: Optional[int] = None
    fecha_creacion: Optional[datetime] = None
    firmado_por_id: Optional[int] = None
    fecha_firma: Optional[datetime] = None

    class Config:
        orm_mode = True

# Schema for the Unified Timeline
class TimelineEvent(BaseModel):
    tipo: str # "NOTA", "TURNO"
    fecha: datetime
    descripcion: str # "Evolución Dr. X" or "Tomografía de Torax"
    detalle: Optional[str] = "" # The note text or extra info about the turno (status, etc)
    id_referencia: Optional[int] # ID of the note or the turno
    estado: Optional[str] = None # For turnos: "Asistido", "Ausente", etc.
    servicio: Optional[str] = None
    medico_nombre: Optional[str] = None
    medico_matricula: Optional[str] = None
    structured_content: Optional[dict] = None # For structured history fields

from schemas.paciente import PacienteOut

class TimelineResponse(BaseModel):
    paciente_id: int
    paciente: Optional[PacienteOut] = None
    timeline: List[TimelineEvent]
