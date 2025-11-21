from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from database import get_db
from models.user import User
from schemas.user import UserCreate, UserOut
from auth.jwt import create_access_token  # ✅ Import correcto

router = APIRouter(prefix="/users", tags=["Users"])

# Configuración para hashear contraseñas
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# 🔐 Función para verificar contraseñas
def verificar_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


# 🔐 Función para hashear contraseñas
def get_password_hash(password):
    return pwd_context.hash(password)


# 🧩 Registrar nuevo usuario
@router.post("/register", response_model=UserOut)
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    # Verificar si el usuario ya existe
    existing_user = db.query(User).filter(User.username == user.username).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El nombre de usuario ya existe."
        )

    hashed_password = get_password_hash(user.password)
    new_user = User(username=user.username, password=hashed_password, role=user.role)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


# 🔑 Login de usuario
@router.post("/login")
def login_user(user: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.username == user.username).first()

    if not db_user:
        raise HTTPException(status_code=400, detail="Usuario o contraseña incorrectos")

    if not verificar_password(user.password, db_user.password):
        raise HTTPException(status_code=400, detail="Usuario o contraseña incorrectos")

    # ✅ Crear el token JWT
    token = create_access_token({"sub": db_user.username, "role": db_user.role})

    return {"access_token": token, "token_type": "bearer"}
