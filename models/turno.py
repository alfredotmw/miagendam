from sqlalchemy import Column, Integer, DateTime, ForeignKey, String
from sqlalchemy.orm import relationship
from database import Base

class Turno(Base):
    __tablename__ = "turnos"

    id = Column(Integer, primary_key=True, index=True)
    fecha = Column(DateTime, nullable=False)
    hora = Column(String, nullable=False)
    duracion = Column(Integer, nullable=True) # Duración en minutos

    paciente_id = Column(Integer, ForeignKey("pacientes.id"), nullable=False)
    agenda_id = Column(Integer, ForeignKey("agendas.id"), nullable=False)
    practica_id = Column(Integer, ForeignKey("practicas.id"), nullable=True)
    medico_derivante_id = Column(Integer, ForeignKey("medicos_derivantes.id"), nullable=True)

    paciente = relationship("Paciente", back_populates="turnos")
    agenda = relationship("Agenda", back_populates="turnos")
    practica = relationship("Practica", back_populates="turnos")
    medico_derivante = relationship("MedicoDerivante", back_populates="turnos")

    estado = Column(String, default="pendiente")

