from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime

class HistoriaClinica(Base):
    __tablename__ = "historia_clinica"

    id = Column(Integer, primary_key=True, index=True)
    paciente_id = Column(Integer, ForeignKey("pacientes.id"), nullable=False)
    medico_id = Column(Integer, ForeignKey("users.id"), nullable=True) # Opcional: si queremos saber quien escribio
    
    fecha = Column(DateTime, default=datetime.now)
    texto = Column(Text, nullable=False)
    servicio = Column(String, nullable=False) # CONSULTORIO, QUIMIOTERAPIA, ETC.

    # Relaciones
    paciente = relationship("Paciente", back_populates="historia_clinica")
    medico = relationship("User", backref="historias_creadas") # Backref simple para usuario
