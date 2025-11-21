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
