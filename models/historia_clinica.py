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
    texto = Column(Text, nullable=True) # Mantener como fallback o resumen
    servicio = Column(String, nullable=False) # CONSULTORIO, QUIMIOTERAPIA, ETC.

    # Campos Estructurados (Ley 26.529 / Requerimiento User)
    motivo_consulta = Column(Text, nullable=True)
    antecedentes = Column(Text, nullable=True) # Personales, Familiares, Enfermedad Actual
    examen_clinico = Column(Text, nullable=True) # Incluye Diagnostico Probable
    plan_estudio = Column(Text, nullable=True)
    diagnostico_diferencial = Column(Text, nullable=True)
    tratamiento = Column(Text, nullable=True)
    evolucion = Column(Text, nullable=True) # Pronostico y Evolucion

    # Relaciones
    paciente = relationship("Paciente", back_populates="historia_clinica")
    medico = relationship("User", backref="historias_creadas") # Backref simple para usuario
