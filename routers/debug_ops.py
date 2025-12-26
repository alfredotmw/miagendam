from fastapi import APIRouter, Depends
from sqlalchemy import text, inspect
from sqlalchemy.orm import Session
from database import get_db, engine

router = APIRouter(prefix="/debug", tags=["Debug"])

@router.get("/db-info")
def get_db_info(db: Session = Depends(get_db)):
    """
    Returns schema info for 'users' table and details for user 'Alfredo'.
    """
    info = {}
    
    # 1. Inspect Columns
    try:
        inspector = inspect(engine)
        if inspector.has_table("users"):
            columns = [col["name"] for col in inspector.get_columns("users")]
            info["users_table_columns"] = columns
        else:
            info["users_table_columns"] = "Table 'users' NOT FOUND"
    except Exception as e:
        info["inspection_error"] = str(e)

    # 2. Check User 'Alfredo'
    try:
        result = db.execute(text("SELECT id, username, role, allowed_agendas FROM users WHERE username = 'Alfredo'")).fetchone()
        if result:
            info["user_alfredo"] = {
                "id": result[0],
                "username": result[1],
                "role": result[2],
                "allowed_agendas": result[3]
            }
        else:
            info["user_alfredo"] = "User 'Alfredo' not found"
    except Exception as e:
        info["query_error"] = str(e)
        
    return info

@router.get("/fix-schema")
def fix_schema_manual():
    """
    Manually attempts to add the 'allowed_agendas' column to the 'users' table.
    """
    log = []
    try:
        inspector = inspect(engine)
        columns = [col["name"] for col in inspector.get_columns("users")]
        
        if "allowed_agendas" not in columns:
            log.append("Column 'allowed_agendas' missing. Attempting to add...")
            with engine.connect() as conn:
                conn.execute(text("ALTER TABLE users ADD COLUMN allowed_agendas VARCHAR"))
                conn.commit()
            log.append("✅ Success: Column added.")
        else:
            log.append("ℹ️ Info: Column 'allowed_agendas' already exists.")
            
    except Exception as e:
        log.append(f"❌ Error: {str(e)}")
        
    return {"log": log}
