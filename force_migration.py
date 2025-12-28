from sqlalchemy import create_engine, text
from sqlalchemy.engine import reflection

DATABASE_URL = "sqlite:///./agendas.db"
engine = create_engine(DATABASE_URL)

def check_column_exists(engine, table_name, column_name, alter_statement):
    inspector = reflection.Inspector.from_engine(engine)
    columns = [col['name'] for col in inspector.get_columns(table_name)]
    if column_name not in columns:
        print(f"⚠️ Column '{column_name}' missing in '{table_name}'. Applying migration...")
        with engine.connect() as conn:
            conn.execute(text(alter_statement))
            print(f"✅ Executed: {alter_statement}")
    else:
        print(f"✅ Column '{column_name}' already exists in '{table_name}'.")

print("Checking and applying migrations manually...")
try:
    check_column_exists(engine, "historia_clinica", "requiere_radioterapia", "ALTER TABLE historia_clinica ADD COLUMN requiere_radioterapia BOOLEAN DEFAULT 0")
    print("✅ Migration process finished.")
except Exception as e:
    print(f"❌ Error applying migration: {e}")
