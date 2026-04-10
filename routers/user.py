from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
from models.user import User, UserRole
from models.agenda import Agenda
import bcrypt
from typing import List, Optional
from auth.jwt import create_access_token, get_current_user, require_roles
from pydantic import BaseModel

router = APIRouter(prefix="/users", tags=["Users"])



# 🧱 Modelos Pydantic
class UserCreate(BaseModel):
    username: str
    password: str
    role: UserRole
    allowed_agendas: Optional[str] = None # IDs separated by comma
    matricula: Optional[str] = None
    full_name: Optional[str] = None
    especialidad: Optional[str] = None


class UserLogin(BaseModel):
    username: str
    password: str


class UserResponse(BaseModel):
    id: int
    username: str
    role: UserRole
    allowed_agendas: Optional[str] = None
    matricula: Optional[str] = None
    full_name: Optional[str] = None
    especialidad: Optional[str] = None

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
        allowed_agendas=user.allowed_agendas,
        matricula=user.matricula,
        full_name=user.full_name
    )
    db.add(db_user)
    
    # 🛡️ Synchronize Many-to-Many relationship from legacy CSV string
    if user.allowed_agendas:
        try:
            agenda_ids = [int(id.strip()) for id in user.allowed_agendas.split(',') if id.strip()]
            if agenda_ids:
                agendas = db.query(Agenda).filter(Agenda.id.in_(agenda_ids)).all()
                db_user.agendas = agendas
        except ValueError:
            pass # Ignore malformed CSV for now
            
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
        "id": db_user.id,
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


# ✏️ Editar Usuario
class UserUpdate(BaseModel):
    role: Optional[UserRole] = None
    allowed_agendas: Optional[str] = None
    matricula: Optional[str] = None
    full_name: Optional[str] = None
    especialidad: Optional[str] = None
    password: Optional[str] = None # Opcional: Permitir reset de password

@router.put("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int,
    user_update: UserUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_roles(["ADMIN"]))
):
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    if user_update.role:
        db_user.role = user_update.role
    
    # Sincronizar relación Many-to-Many si cambió allowed_agendas
    if user_update.allowed_agendas is not None:
        db_user.allowed_agendas = user_update.allowed_agendas
        try:
            if user_update.allowed_agendas.strip():
                agenda_ids = [int(id.strip()) for id in user_update.allowed_agendas.split(',') if id.strip()]
                agendas = db.query(Agenda).filter(Agenda.id.in_(agenda_ids)).all()
                db_user.agendas = agendas
            else:
                db_user.agendas = []
        except ValueError:
            pass

    if user_update.matricula is not None:
        db_user.matricula = user_update.matricula
        
    if user_update.full_name is not None:
        db_user.full_name = user_update.full_name

    if user_update.password:
        hashed_password = bcrypt.hashpw(user_update.password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        db_user.password = hashed_password

    db.commit()
    db.refresh(db_user)
    return db_user


# 🗑️ Eliminar Usuario (Solo ADMIN)
@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_roles(["ADMIN"]))
):
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    # Prevent self-deletion (optional but good practice)
    if db_user.username == current_user["username"]:
        raise HTTPException(status_code=400, detail="No puedes eliminar tu propio usuario")

    db.delete(db_user)
    db.commit()
    return None
