from database import engine
from sqlalchemy import text, inspect
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def add_oncology_columns():
    inspector = inspect(engine)
    table_name = "historia_clinica"
    
    if not inspector.has_table(table_name):
        logger.error(f"❌ Table '{table_name}' does not exist.")
        return

    columns = [col["name"] for col in inspector.get_columns(table_name)]
    
    # Define new columns
    new_columns = {
        "ecog": "INTEGER",
        "tnm": "VARCHAR",
        "estadio": "VARCHAR",
        "toxicidad": "TEXT"
    }

    with engine.connect() as conn:
        for col_name, col_type in new_columns.items():
            if col_name not in columns:
                logger.info(f"Adding column '{col_name}'...")
                try:
                    conn.execute(text(f"ALTER TABLE {table_name} ADD COLUMN {col_name} {col_type}"))
                    conn.commit()
                    logger.info(f"✅ Column '{col_name}' added.")
                except Exception as e:
                    logger.error(f"❌ Failed to add '{col_name}': {e}")
            else:
                logger.info(f"ℹ️ Column '{col_name}' already exists.")

    logger.info("🎉 P1 Oncology Migration completed.")

if __name__ == "__main__":
    add_oncology_columns()
