from fastapi import APIRouter, Depends
import io
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

@router.get("/fix-schema-all")
def fix_schema_all():
    """ Runs the full check_and_migrate_db logic from migration_utils. """
    from migration_utils import check_and_migrate_db, logger
    import logging
    import io
    
    # Capture logs
    log_capture_string = io.StringIO()
    ch = logging.StreamHandler(log_capture_string)
    ch.setLevel(logging.INFO)
    logger.addHandler(ch)

    status = "Started"
    try:
        check_and_migrate_db(engine)
        status = "Completed"
    except Exception as e:
        status = f"Error: {e}"
        logger.error(f"Migration error: {e}")
    
    log_contents = log_capture_string.getvalue()
    logger.removeHandler(ch)
    
    # Inspector check for specific columns
    inspector = inspect(engine)
    cols_turnos = []
    if inspector.has_table("turnos"):
        cols_turnos = [c["name"] for c in inspector.get_columns("turnos")]

    cols_hc = []
    if inspector.has_table("historia_clinica"):
        cols_hc = [c["name"] for c in inspector.get_columns("historia_clinica")]

    return {
        "status": status,
        "turnos_columns": cols_turnos,
        "historia_clinica_columns": cols_hc,
        "logs": log_contents
    }

@router.delete("/wipe-radioterapia")
def wipe_radioterapia(db: Session = Depends(get_db)):
    """
    ⚠️ DANGER: Deletes ALL records from SeguimientoRadioterapia table.
    Used for testing "from scratch".
    """
    try:
        db.execute(text("DELETE FROM seguimiento_radioterapia"))
        db.commit()
        return {"status": "success", "message": "All Radiotherapy Tracking data wiped."}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@router.delete("/wipe-all")
def wipe_all_data(db: Session = Depends(get_db)):
    """
    ⚠️ DANGER: Deletes ALL Patient Data (Pacientes, Turnos, HC, Seguimiento).
    DOES NOT delete Users, Agendas, Practicas, Obras Sociales.
    """
    try:
        # 1. Tablas dependientes (Hijas)
        db.execute(text("DELETE FROM turnos_practicas")) 
        db.execute(text("DELETE FROM seguimiento_radioterapia"))
        db.execute(text("DELETE FROM historia_clinica"))
        
        # 2. Tablas principales (Padres)
        db.execute(text("DELETE FROM turnos")) 
        db.execute(text("DELETE FROM pacientes"))
        # Note: Users and Doctors are NOT wiped.
        
        db.commit()
        return {"status": "success", "message": "ALL Patient data wiped (Clean Slate)."}
    except Exception as e:
        db.rollback()
        return {"status": "error", "message": str(e)}
