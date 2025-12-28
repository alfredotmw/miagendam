from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import os

# Adjust DB URL as needed
DATABASE_URL = "sqlite:///./agendas.db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db = SessionLocal()

print("--- AGENDAS ---")
agendas = db.execute(text("SELECT id, nombre, tipo FROM agendas")).fetchall()
for a in agendas:
    print(a)

print("\n--- PRACTICAS (Filtered by name like TAC) ---")
practicas = db.execute(text("SELECT id, nombre, categoria FROM practicas WHERE nombre LIKE '%TAC%' OR nombre LIKE '%MARCACION%'")).fetchall()
for p in practicas:
    print(p)
