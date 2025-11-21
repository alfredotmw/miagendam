from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

import os

# Nombre de tu base de datos (sqlite)
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./agendas.db")

# Si es PostgreSQL (Render usa postgres:// pero SQLAlchemy necesita postgresql://)
if SQLALCHEMY_DATABASE_URL.startswith("postgres://"):
    SQLALCHEMY_DATABASE_URL = SQLALCHEMY_DATABASE_URL.replace("postgres://", "postgresql://", 1)

connect_args = {}
if "sqlite" in SQLALCHEMY_DATABASE_URL:
    connect_args = {"check_same_thread": False}

# Crea el motor de conexión
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args=connect_args
)

# Crea la sesión
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base para los modelos
Base = declarative_base()


# ✅ Esta función es la que faltaba
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
