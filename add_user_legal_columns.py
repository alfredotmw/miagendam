from database import engine
from sqlalchemy import text

def migrate_users_columns():
    with engine.connect() as conn:
        try:
            # 1. Add matricula
            try:
                conn.execute(text("ALTER TABLE users ADD COLUMN matricula VARCHAR"))
                print("✅ Column 'matricula' added.")
            except Exception as e:
                print(f"⚠️ Column 'matricula' might exist: {e}")

            # 2. Add full_name
            try:
                conn.execute(text("ALTER TABLE users ADD COLUMN full_name VARCHAR"))
                print("✅ Column 'full_name' added.")
            except Exception as e:
                print(f"⚠️ Column 'full_name' might exist: {e}")
                
            conn.commit()
            print("🚀 Migration for User Legal Fields completed.")
        except Exception as e:
            print(f"❌ Migration failed: {e}")

if __name__ == "__main__":
    migrate_users_columns()
