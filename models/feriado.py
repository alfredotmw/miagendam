# models/feriado.py
"""Feriados y días sin servicio, para agendar tratamientos de lunes a viernes.

Tabla propia (feriados): no toca `turnos` ni ningún modelo existente. La crea
Base.metadata.create_all() al arrancar. Nunca se borran filas: se desactivan.
"""
from datetime import datetime
from sqlalchemy import Boolean, Column, Date, DateTime, Integer, String
from database import Base


class Feriado(Base):
    __tablename__ = "feriados"

    id = Column(Integer, primary_key=True, index=True)
    fecha = Column(Date, nullable=False, unique=True, index=True)
    nombre = Column(String(200), nullable=False)
    tipo = Column(String(40), nullable=False, default="feriado")      # inamovible, trasladable, puente, sin_servicio...
    origen = Column(String(20), nullable=False, default="nacional")   # nacional | manual
    activo = Column(Boolean, nullable=False, default=True)
    creado_por_id = Column(Integer, nullable=True)
    fecha_creacion = Column(DateTime, nullable=False, default=datetime.now)
    modificado_por_id = Column(Integer, nullable=True)
    fecha_modificacion = Column(DateTime, nullable=True)
