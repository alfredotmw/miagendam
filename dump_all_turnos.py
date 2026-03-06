from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "sqlite:///./agendas.db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db = SessionLocal()

print("Dumping all turnos...")
query = text("SELECT * FROM turnos")
results = db.execute(query).fetchall()
cols = db.execute(text("PRAGMA table_info(turnos)")).fetchall()
col_names = [c[1] for c in cols]

with open("all_turnos_dump.txt", "w", encoding="utf-8") as f:
    f.write("\t".join(col_names) + "\n")
    for r in results:
        f.write("\t".join(map(str, r)) + "\n")
print(f"Dumped {len(results)} turnos.")
