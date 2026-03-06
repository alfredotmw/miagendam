from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "sqlite:///./agendas.db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db = SessionLocal()

print("--- RAW TURNOS (last 20) ---")
query = text("""
    SELECT * FROM turnos ORDER BY id DESC LIMIT 20
""")
results = db.execute(query).fetchall()
cols = db.execute(text("PRAGMA table_info(turnos)")).fetchall()
col_names = [c[1] for c in cols]

for r in results:
    print(dict(zip(col_names, r)))
