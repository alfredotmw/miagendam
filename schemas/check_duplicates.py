from datetime import date
from typing import List
from pydantic import BaseModel

class CheckDuplicates(BaseModel):
    paciente_id: int
    fechas: List[date]
