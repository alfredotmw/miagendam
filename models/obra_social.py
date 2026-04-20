from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime

class ObraSocial(Base):
    __tablename__ = "obras_sociales"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, unique=True, nullable=False)
    codigo = Column(String, unique=True, nullable=True)
    descripcion = Column(String, nullable=True)

    # Auditoría
    creado_por_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    fecha_creacion = Column(DateTime, default=datetime.now)
    modificado_por_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    fecha_modificacion = Column(DateTime, nullable=True, onupdate=datetime.now)

    creado_por = relationship("User", foreign_keys=[creado_por_id])
    modificado_por = relationship("User", foreign_keys=[modificado_por_id])

    pacientes = relationship("Paciente", back_populates="obra_social")

