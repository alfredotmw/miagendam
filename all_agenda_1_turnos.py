from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "sqlite:///./agendas.db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db = SessionLocal()

print("--- ALL TURNOS FOR AGENDA 1 (QUIMIOTERAPIA SAN MARTIN) ---")
query = text("""
    SELECT t.id, t.fecha, t.hora, t.paciente_id, p.nombre, p.apellido, t.practica_id 
    FROM turnos t
    LEFT JOIN pacientes p ON t.paciente_id = p.id
    WHERE t.agenda_id = 1
    ORDER BY t.fecha DESC
""")
results = db.execute(query).fetchall()
for r in results:
    print(r)
