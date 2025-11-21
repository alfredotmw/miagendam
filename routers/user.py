from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
from models.user import User, UserRole
from passlib.context import CryptContext
from auth.jwt import create_access_token
from pydantic import BaseModel

router = APIRouter(prefix="/users", tags=["Users"])

# Contexto de hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# 🧱 Modelos Pydantic
class UserCreate(BaseModel):
    username: str
    password: str
    role: UserRole


class UserLogin(BaseModel):
    username: str
    password: str


class UserResponse(BaseModel):
    id: int
    username: str
    role: UserRole

    class Config:
        from_attributes = True  # ✅ Compatible con Pydantic v2


# 🧩 Registrar nuevo usuario
@router.post("/register", response_model=UserResponse)
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.username == user.username).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="El usuario ya existe")

    hashed_password = pwd_context.hash(user.password)
    db_user = User(username=user.username, password=hashed_password, role=user.role)
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

    if not pwd_context.verify(user.password, db_user.password):
        raise HTTPException(status_code=401, detail="Contraseña incorrecta")

    token_data = {"sub": db_user.username, "role": db_user.role}
    access_token = create_access_token(token_data)

    return {"access_token": access_token, "token_type": "bearer"}
