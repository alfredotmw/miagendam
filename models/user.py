from sqlalchemy import Column, Integer, String, Enum as SqlEnum
from database import Base
from enum import Enum


class UserRole(str, Enum):
    ADMIN = "ADMIN"
    MEDICO = "MEDICO"
    RECEPCION = "RECEPCION"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
    role = Column(SqlEnum(UserRole), nullable=False)
    allowed_agendas = Column(String, nullable=True) # Comma separated IDs: "1,2,5"
    matricula = Column(String, nullable=True) # M.N. / M.P.
    full_name = Column(String, nullable=True) # Nombre Real del Profesional
