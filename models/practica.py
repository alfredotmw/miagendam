from sqlalchemy import Column, Integer, String, Enum
from sqlalchemy.orm import relationship
from database import Base
import enum

class CategoriaPractica(str, enum.Enum):
    TOMOGRAFIA = "TOMOGRAFIA"
    RADIOGRAFIA = "RADIOGRAFIA"
    ECOGRAFIA = "ECOGRAFIA"
    PET = "PET"
    ELECTRO_MAPEO = "ELECTRO_MAPEO"
    RADIOTERAPIA = "RADIOTERAPIA"
    CAMARA_GAMMA = "CAMARA_GAMMA"
    QUIMIOTERAPIA = "QUIMIOTERAPIA"
    CONSULTA_MEDICA = "CONSULTA_MEDICA"

class Practica(Base):
    __tablename__ = "practicas"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, nullable=False, index=True)
    categoria = Column(Enum(CategoriaPractica), nullable=False)

    turnos = relationship("Turno", back_populates="practica")

