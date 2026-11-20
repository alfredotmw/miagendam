# models/turno_estudio_archivo.py
"""Informe en PDF de un estudio que no se publica en Visual Médica
(p. ej. ecografía, electroencefalograma): un PDF por turno, guardado en la base.

Igual que turno_estudio_links: tabla separada, sin columnas ni relaciones nuevas en
`turnos`. Se guarda en PostgreSQL y no en disco porque el disco de Render se borra
en cada despliegue. Lo crea create_all() al arrancar.
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, LargeBinary
from database import Base


class TurnoEstudioArchivo(Base):
    __tablename__ = "turno_estudio_archivos"

    id = Column(Integer, primary_key=True, index=True)
    turno_id = Column(Integer, ForeignKey("turnos.id", ondelete="CASCADE"),
                      nullable=False, unique=True, index=True)
    nombre_archivo = Column(String(255), nullable=False)
    tamano_bytes = Column(Integer, nullable=False)
    sha256 = Column(String(64), nullable=False)
    contenido = Column(LargeBinary, nullable=False)
    cargado_por_id = Column(Integer, nullable=True)
    fecha_carga = Column(DateTime, nullable=False, default=datetime.now)
