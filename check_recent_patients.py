from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "sqlite:///./agendas.db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db = SessionLocal()

print("--- LATEST 10 PACIENTES ---")
query = text("""
    SELECT id, nombre, apellido, dni FROM pacientes ORDER BY id DESC LIMIT 10
""")
results = db.execute(query).fetchall()
for r in results:
    print(r)

print("\n--- TURNOS FOR THESE PATIENTS ---")
for p in results:
    p_id = p[0]
    query_t = text("SELECT id, fecha, hora, agenda_id FROM turnos WHERE paciente_id = :p_id")
    res_t = db.execute(query_t, {"p_id": p_id}).fetchall()
    if res_t:
        print(f"Paciente {p_id} ({p[1]} {p[2]}):")
        for t in res_t:
            print(f"  {t}")
