from sqlalchemy import Column, Integer, DateTime, ForeignKey, String, Boolean
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime
from models.user import User # Importamos User para la relación de recordatorio

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
    practicas = relationship("Practica", secondary="turnos_practicas", back_populates="turnos_mult")
    medico_derivante = relationship("MedicoDerivante", back_populates="turnos")

    estado = Column(String, default="pendiente")
    patologia = Column(String, nullable=True)
    observaciones = Column(String, nullable=True)

    # Campos para recordatorios de WhatsApp
    recordatorio_enviado = Column(Boolean, default=False)
    recordatorio_fecha = Column(DateTime, nullable=True)
    recordatorio_usuario_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    # Auditoría
    creado_por_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    fecha_creacion = Column(DateTime, default=datetime.now)
    modificado_por_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    fecha_modificacion = Column(DateTime, nullable=True, onupdate=datetime.now)

    # Relaciones de Auditoría
    creado_por = relationship("User", foreign_keys=[creado_por_id])
    modificado_por = relationship("User", foreign_keys=[modificado_por_id])
    recordatorio_usuario = relationship("User", foreign_keys=[recordatorio_usuario_id])

