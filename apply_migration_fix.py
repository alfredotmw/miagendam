from database import engine
from migration_utils import check_column_exists

print("Checking and applying migrations manually...")

# Migración de Historia Clínica (Radioterapia)
try:
    check_column_exists(engine, "historia_clinica", "requiere_radioterapia", "ALTER TABLE historia_clinica ADD COLUMN requiere_radioterapia BOOLEAN DEFAULT 0")
    print("✅ Migration checked/applied.")
except Exception as e:
    print(f"❌ Error applying migration: {e}")
