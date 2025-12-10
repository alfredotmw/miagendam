# schemas/turno.py

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel
from schemas.practica import PracticaOut
from schemas.paciente import PacienteOut
from schemas.agenda import AgendaOut

class TurnoBase(BaseModel):
    fecha: datetime          # Podés mandar: "2025-11-14T09:00:00"
    hora: str                # También la guardamos como texto "09:00"
    paciente_id: int
    agenda_id: int
    practicas_ids: List[int] # IDs de las prácticas asociadas
    estado: str = "pendiente"
    duracion_custom: Optional[int] = None # Para radioterapia (10 o 20)
    
    # Médico Derivante: puede venir ID o Nombre (para crear)
    medico_derivante_id: Optional[int] = None
    medico_derivante_nombre: Optional[str] = None 
    patologia: Optional[str] = None 

class TurnoCreate(TurnoBase):
    pass

class TurnoUpdate(BaseModel):
    fecha: Optional[datetime] = None
    hora: Optional[str] = None
    estado: Optional[str] = None # completado, ausente, pendiente, cancelado
    duracion: Optional[int] = None
    medico_derivante_id: Optional[int] = None
    patologia: Optional[str] = None

class TurnoOut(BaseModel):
    id: int
    fecha: datetime
    hora: str
    duracion: Optional[int]
    estado: str
    paciente_id: int
    agenda_id: int
    medico_derivante_id: Optional[int]
    patologia: Optional[str]
    practicas: List[PracticaOut]
    
    paciente: Optional[PacienteOut] = None
    agenda: Optional[AgendaOut] = None

    class Config:
        from_attributes = True


