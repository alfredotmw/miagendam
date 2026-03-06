from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "sqlite:///./agendas.db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db = SessionLocal()

def search_value(val):
    print(f"Searching for '{val}'...")
    tables = db.execute(text("SELECT name FROM sqlite_master WHERE type='table'")).fetchall()
    for table_row in tables:
        table_name = table_row[0]
        cols_res = db.execute(text(f"PRAGMA table_info({table_name})")).fetchall()
        cols = [c[1] for c in cols_res]
        
        for col in cols:
            try:
                query = text(f"SELECT * FROM {table_name} WHERE CAST({col} AS TEXT) LIKE :val")
                results = db.execute(query, {"val": f"%{val}%"}).fetchall()
                if results:
                    print(f"[{table_name}.{col}] Found {len(results)} matches.")
                    # print sample
                    for r in results[:3]:
                        print(f"  {r}")
            except Exception:
                pass

search_value("00:00:00")
search_value("2026-02-26")
search_value("26/02/2026")
