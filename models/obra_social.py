from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from database import Base

class ObraSocial(Base):
    __tablename__ = "obras_sociales"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, unique=True, nullable=False)
    codigo = Column(String, unique=True, nullable=True)
    descripcion = Column(String, nullable=True)

    pacientes = relationship("Paciente", back_populates="obra_social")

