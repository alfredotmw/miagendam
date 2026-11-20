# models/turno_estudio_link.py
"""Link al estudio (TAC, PET, ecografía) publicado en el portal externo (Visual Médica).

Tabla separada a propósito: NO se agrega ninguna columna a `turnos` ni relación al
modelo Turno. Así, si esta tabla no existiera, el resto del sistema sigue igual
(la caída del 11/11/2026 fue por una columna nueva en `turnos`).
La tabla la crea Base.metadata.create_all() al arrancar (solo crea tablas faltantes).
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from database import Base


class TurnoEstudioLink(Base):
    __tablename__ = "turno_estudio_links"

    id = Column(Integer, primary_key=True, index=True)
    turno_id = Column(Integer, ForeignKey("turnos.id", ondelete="CASCADE"),
                      nullable=False, unique=True, index=True)
    url = Column(String(500), nullable=False)
    cargado_por_id = Column(Integer, nullable=True)
    fecha_carga = Column(DateTime, nullable=False, default=datetime.now)
    modificado_por_id = Column(Integer, nullable=True)
    fecha_modificacion = Column(DateTime, nullable=True)
