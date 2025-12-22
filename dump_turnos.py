
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models.turno import Turno
from models.paciente import Paciente
from models.agenda import Agenda
from database import SQLALCHEMY_DATABASE_URL
import datetime

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
db = SessionLocal()

print(f"Connecting to: {SQLALCHEMY_DATABASE_URL}")

turnos = db.query(Turno).filter(Turno.fecha >= datetime.datetime(2025, 12, 20)).all()
print(f"Turnos found from 2025-12-20 onwards: {len(turnos)}")

for t in turnos:
    paciente_nombre = t.paciente.nombre if t.paciente else "Sin paciente"
    agenda_nombre = t.agenda.nombre if t.agenda else "Sin agenda"
    print(f"ID: {t.id} | Fecha: {t.fecha} | Hora: {t.hora} | Estado: {t.estado} | Paciente: {paciente_nombre} | Agenda: {agenda_nombre}")

db.close()
