# models/turno_practica.py

from sqlalchemy import Column, Integer, ForeignKey
from database import Base

class TurnoPractica(Base):
    __tablename__ = "turnos_practicas"

    id = Column(Integer, primary_key=True, index=True)
    turno_id = Column(Integer, ForeignKey("turnos.id", ondelete="CASCADE"), nullable=False)
    practica_id = Column(Integer, ForeignKey("practicas.id", ondelete="CASCADE"), nullable=False)
