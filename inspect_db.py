from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import os

DATABASE_URL = "sqlite:///./agendas.db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db = SessionLocal()

print("--- AGENDAS ---")
agendas = db.execute(text("SELECT id, nombre, tipo FROM agendas")).fetchall()
for a in agendas:
    print(a)

print("\n--- COUNT TURNOS ---")
count = db.execute(text("SELECT count(*) FROM turnos")).scalar()
print(f"Total turnos: {count}")

print("\n--- ULTIMOS 5 TURNOS ---")
turnos = db.execute(text("SELECT id, fecha, hora, paciente_id, agenda_id FROM turnos ORDER BY id DESC LIMIT 5")).fetchall()
for t in turnos:
    print(t)
