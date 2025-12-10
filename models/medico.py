from sqlalchemy import Column, Integer, String
from database import Base

class MedicoDerivante(Base):
    __tablename__ = "medicos_derivantes"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, unique=True, index=True)
    matricula = Column(String, nullable=True)
    telefono = Column(String, nullable=True)

    from sqlalchemy.orm import relationship
    turnos = relationship("Turno", back_populates="medico_derivante")
