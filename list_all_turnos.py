
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models.turno import Turno
from database import SQLALCHEMY_DATABASE_URL

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
db = SessionLocal()

turnos = db.query(Turno).order_by(Turno.id.desc()).all()

with open("turnos_log.txt", "w", encoding="utf-8") as f:
    f.write(f"Total turnos: {len(turnos)}\n")
    for t in turnos:
        paciente = t.paciente.nombre if t.paciente else "Sin paciente"
        agenda = t.agenda.nombre if t.agenda else "Sin agenda"
        f.write(f"ID: {t.id} | Fecha: {t.fecha} | Hora: {t.hora} | Estado: {t.estado} | Paciente: {paciente} | Agenda: {agenda}\n")

db.close()
print("Log written to turnos_log.txt")
