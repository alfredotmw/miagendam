from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "sqlite:///./agendas.db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db = SessionLocal()

print("--- TURNOS WITH QUIMIOTERAPIA PRACTICES (54, 55, 66) ---")
query = text("""
    SELECT t.id, t.fecha, t.hora, t.agenda_id, a.nombre as agenda_nombre, p.nombre, p.apellido, pr.nombre as practica_nombre
    FROM turnos t
    JOIN turno_practica tp ON t.id = tp.turno_id
    JOIN practicas pr ON tp.practica_id = pr.id
    JOIN agendas a ON t.agenda_id = a.id
    JOIN pacientes p ON t.paciente_id = p.id
    WHERE pr.id IN (54, 55, 66)
    ORDER BY t.fecha DESC
""")
results = db.execute(query).fetchall()
for r in results:
    print(r)
""")
