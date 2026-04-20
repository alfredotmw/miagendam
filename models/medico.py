from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from database import Base
from datetime import datetime
from sqlalchemy.orm import relationship

class MedicoDerivante(Base):
    __tablename__ = "medicos_derivantes"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, unique=True, index=True)
    matricula = Column(String, nullable=True)
    telefono = Column(String, nullable=True)

    # Auditoría
    creado_por_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    fecha_creacion = Column(DateTime, default=datetime.now)
    modificado_por_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    fecha_modificacion = Column(DateTime, nullable=True, onupdate=datetime.now)

    creado_por = relationship("User", foreign_keys=[creado_por_id])
    modificado_por = relationship("User", foreign_keys=[modificado_por_id])

    turnos = relationship("Turno", back_populates="medico_derivante")
