from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "sqlite:///./agendas.db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db = SessionLocal()

print("--- ALL TURNOS ON 2026-02-26 ---")
query = text("""
    SELECT t.id, t.fecha, t.hora, t.agenda_id, a.nombre as agenda_nombre, p.nombre, p.apellido
    FROM turnos t
    JOIN agendas a ON t.agenda_id = a.id
    JOIN pacientes p ON t.paciente_id = p.id
    WHERE t.fecha LIKE '%2026-02-26%'
""")
results = db.execute(query).fetchall()
for r in results:
    print(r)

print("\n--- ANY TURNOS WITH HORA '00:00:00' ---")
query2 = text("""
    SELECT t.id, t.fecha, t.hora, t.agenda_id, a.nombre as agenda_nombre, p.nombre, p.apellido
    FROM turnos t
    JOIN agendas a ON t.agenda_id = a.id
    JOIN pacientes p ON t.paciente_id = p.id
    WHERE t.hora LIKE '00:00%'
""")
results2 = db.execute(query2).fetchall()
for r in results2:
    print(r)
""")
# Also check if there are any appointments for that day regardless of format
all_feb_26 = db.execute(text("SELECT id, fecha, hora, agenda_id FROM turnos WHERE fecha LIKE '%02-26%'")).fetchall()
print(f"\nTotal turnos in Feb 26 (any year): {len(all_feb_26)}")
for r in all_feb_26:
    print(r)
