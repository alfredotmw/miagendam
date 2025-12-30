from sqlalchemy import create_engine, inspect
import os

DATABASE_URL = "sqlite:///./agendas.db"
engine = create_engine(DATABASE_URL)

def check_columns():
    inspector = inspect(engine)
    if inspector.has_table("turnos"):
        print("--- COLUMNS IN 'turnos' ---")
        cols = inspector.get_columns("turnos")
        found = False
        for c in cols:
            print(f"- {c['name']} ({c['type']})")
            if c['name'] == 'patologia':
                found = True
        
        if found:
            print("\n✅ 'patologia' column FOUND.")
        else:
            print("\n❌ 'patologia' column MISSING.")
    else:
        print("Table 'turnos' not found.")

if __name__ == "__main__":
    check_columns()
