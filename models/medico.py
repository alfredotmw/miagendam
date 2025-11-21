from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from database import Base

class MedicoDerivante(Base):
    __tablename__ = "medicos_derivantes"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, nullable=False, unique=True) # Nombre completo
    matricula = Column(String, nullable=True)
    telefono = Column(String, nullable=True)
    email = Column(String, nullable=True)

    # Relación con turnos
    turnos = relationship("Turno", back_populates="medico_derivante")
