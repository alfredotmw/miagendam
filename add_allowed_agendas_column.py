from database import engine
from sqlalchemy import text

def add_column():
    with engine.connect() as conn:
        try:
            conn.execute(text("ALTER TABLE users ADD COLUMN allowed_agendas VARCHAR"))
            print("✅ Column 'allowed_agendas' added successfully.")
        except Exception as e:
            print(f"⚠️ Error (maybe exists): {e}")

if __name__ == "__main__":
    add_column()
