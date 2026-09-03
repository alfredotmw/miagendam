# models/informe_clinico.py

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime, timezone

def utc_now():
    return datetime.now(timezone.utc)

class InformeClinico(Base):
    __tablename__ = "informes_clinicos"

    id = Column(Integer, primary_key=True, index=True)
    turno_id = Column(Integer, ForeignKey("turnos.id", ondelete="RESTRICT"), nullable=False, unique=True)
    paciente_id = Column(Integer, ForeignKey("pacientes.id"), nullable=False)
    tipo_informe = Column(String(50), nullable=False) # IMAGENES, ELECTROENCEFALOGRAMA, CONSULTA_MEDICA, TEXTO_LIBRE
    contenido_json = Column(JSON, nullable=False)
    contenido_texto = Column(Text, nullable=True)
    estado = Column(String(50), nullable=False, default="BORRADOR") # BORRADOR, FINALIZADO, RECTIFICADO, ANULADO
    version = Column(Integer, nullable=False, default=1)
    
    # Audit timestamps stored in UTC
    created_at = Column(DateTime, nullable=False, default=utc_now)
    updated_at = Column(DateTime, nullable=False, default=utc_now, onupdate=utc_now)
    finalized_at = Column(DateTime, nullable=True)

    # Creator, modifier and finalizer user references
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    updated_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    finalized_by = Column(Integer, ForeignKey("users.id"), nullable=True)

    # Relationships
    turno = relationship("Turno", backref="informe_clinico")
    paciente = relationship("Paciente")
    creador = relationship("User", foreign_keys=[created_by])
    modificador = relationship("User", foreign_keys=[updated_by])
    finalizador = relationship("User", foreign_keys=[finalized_by])
