from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "sqlite:///./agendas.db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db = SessionLocal()

print("--- TURNOS ID 80 TO 100 ---")
query = text("""
    SELECT t.id, t.fecha, t.hora, t.agenda_id, a.nombre as agenda_nombre, p.nombre, p.apellido
    FROM turnos t
    LEFT JOIN agendas a ON t.agenda_id = a.id
    LEFT JOIN pacientes p ON t.paciente_id = p.id
    WHERE t.id >= 80
    ORDER BY t.id ASC
""")
results = db.execute(query).fetchall()
for r in results:
    print(r)
