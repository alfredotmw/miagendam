# models/agenda.py

from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from database import Base

class Agenda(Base):
    __tablename__ = "agendas"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, nullable=False)
    tipo = Column(String, nullable=False)       # MEDICO, TOMOGRAFIA, etc.
    profesional = Column(String, nullable=True) # Solo para consultorios
    slot_minutos = Column(Integer, default=20)
    activo = Column(Integer, default=1) # Usamos Integer como Boolean (1=True, 0=False) para mayor compatibilidad

    # Relación de agenda → turnos (correcta)
    turnos = relationship("Turno", back_populates="agenda")

