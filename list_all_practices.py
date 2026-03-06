from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "sqlite:///./agendas.db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db = SessionLocal()

print("--- ALL PRACTICES ---")
query = text("SELECT id, nombre, categoria FROM practicas")
results = db.execute(query).fetchall()
for r in results:
    print(r)
