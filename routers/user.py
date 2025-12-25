from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
from models.user import User, UserRole
import bcrypt
from typing import List
from auth.jwt import create_access_token, get_current_user, require_roles
from pydantic import BaseModel

router = APIRouter(prefix="/users", tags=["Users"])



# 🧱 Modelos Pydantic
class UserCreate(BaseModel):
    username: str
    password: str
    role: UserRole
    allowed_agendas: str = None # IDs separated by comma


class UserLogin(BaseModel):
    username: str
    password: str


class UserResponse(BaseModel):
    id: int
    username: str
    role: UserRole
    allowed_agendas: str = None

    class Config:
        from_attributes = True  # ✅ Compatible con Pydantic v2


# 🧩 Registrar nuevo usuario (Protegido: Solo ADMIN puede crear usuarios)
@router.post("/register", response_model=UserResponse)
def register_user(
    user: UserCreate, 
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_roles(["ADMIN"])) # 🔒 Solo admins crean usuarios
):
    existing_user = db.query(User).filter(User.username == user.username).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="El usuario ya existe")

    hashed_password = bcrypt.hashpw(user.password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    db_user = User(
        username=user.username, 
        password=hashed_password, 
        role=user.role,
        allowed_agendas=user.allowed_agendas
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


# 🔑 Login de usuario
@router.post("/login")
def login_user(user: UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.username == user.username).first()
    if not db_user:
        raise HTTPException(status_code=401, detail="Usuario no encontrado")

    if not bcrypt.checkpw(user.password.encode('utf-8'), db_user.password.encode('utf-8')):
        raise HTTPException(status_code=401, detail="Contraseña incorrecta")

    token_data = {
        "sub": db_user.username, 
        "role": db_user.role, 
        "allowed_agendas": db_user.allowed_agendas
    }
    access_token = create_access_token(token_data)

    return {"access_token": access_token, "token_type": "bearer"}


# 👤 Obtener usuario actual
@router.get("/me", response_model=UserResponse)
def read_users_me(current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == current_user["username"]).first()
    if user is None:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return user


# 📋 Listar usuarios (Solo ADMIN)
@router.get("/", response_model=List[UserResponse])
def read_users(
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db), 
    current_user: dict = Depends(require_roles(["ADMIN"]))
):
    users = db.query(User).offset(skip).limit(limit).all()
    return users
