from pydantic import BaseModel
from enum import Enum


# Enumeración de roles
class UserRole(str, Enum):
    ADMIN = "ADMIN"
    MEDICO = "MEDICO"
    RECEPCION = "RECEPCION"


# Esquema para registrar un usuario
class UserCreate(BaseModel):
    username: str
    password: str
    role: UserRole


# Esquema para login
class UserLogin(BaseModel):
    username: str
    password: str
    role: UserRole


# Esquema de respuesta (para mostrar usuario creado)
class UserResponse(BaseModel):
    id: int
    username: str
    role: UserRole

    class Config:
        from_attributes = True  # ✅ Pydantic v2 (antes era orm_mode=True)
