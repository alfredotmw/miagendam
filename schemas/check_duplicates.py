from datetime import date
from typing import List, Optional
from pydantic import BaseModel

class CheckDuplicates(BaseModel):
    paciente_id: int
    fechas: List[date]
    agenda_id: Optional[int] = None
