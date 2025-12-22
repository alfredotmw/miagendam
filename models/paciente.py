from sqlalchemy import Column, Integer, String, Date, ForeignKey
from sqlalchemy.orm import relationship
from database import Base

class Paciente(Base):
    __tablename__ = "pacientes"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, nullable=False)
    apellido = Column(String, nullable=False)
    dni = Column(String, unique=True, nullable=False)
    fecha_nacimiento = Column(Date, nullable=True)
    sexo = Column(String, nullable=True) # F, M, X, etc.
    telefono = Column(String, nullable=True) # Mantenemos telefono como genérico
    celular = Column(String, nullable=True)  # Campo específico para celular (WhatsApp)
    email = Column(String, nullable=True)
    direccion = Column(String, nullable=True)
    obra_social_id = Column(Integer, ForeignKey("obras_sociales.id"), nullable=True)

    # Relaciones
    obra_social = relationship("ObraSocial", back_populates="pacientes")

    
    # Nueva relación para Historia Clínica
    historia_clinica = relationship("HistoriaClinica", back_populates="paciente", cascade="all, delete-orphan")
    turnos = relationship("Turno", back_populates="paciente")
