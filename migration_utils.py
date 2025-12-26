import logging
from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine

logger = logging.getLogger(__name__)

def check_and_migrate_db(engine: Engine):
    """
    Verifica si faltan columnas en la base de datos y las agrega.
    Esto es una migración simple 'manual' para evitar usar Alembic por ahora.
    """
    inspector = inspect(engine)
    
    # 1. Verificar tabla 'turnos'
    if inspector.has_table("turnos"):
        columns = [col["name"] for col in inspector.get_columns("turnos")]
        
        # Chequear columna 'patologia'
        if "patologia" not in columns:
            logger.info("⚠️ Columna 'patologia' faltante en 'turnos'. Agregando...")
            with engine.connect() as conn:
                conn.execute(text("ALTER TABLE turnos ADD COLUMN patologia VARCHAR"))
                conn.commit()
            logger.info("✅ Columna 'patologia' agregada exitosamente.")
        else:
            logger.info("✅ Columna 'patologia' ya existe en 'turnos'.")

        # Chequear columna 'duracion' (por si acaso falto en deploy anteriores)
        if "duracion" not in columns:
            logger.info("⚠️ Columna 'duracion' faltante en 'turnos'. Agregando...")
            with engine.connect() as conn:
                conn.execute(text("ALTER TABLE turnos ADD COLUMN duracion INTEGER"))
                conn.commit()
            logger.info("✅ Columna 'duracion' agregada exitosamente.")

        # --- NOTIFICACIONES WHATSAPP ---
        if "recordatorio_enviado" not in columns:
            logger.info("⚠️ Columna 'recordatorio_enviado' faltante. Agregando...")
            with engine.connect() as conn:
                # Determinar si es Postgres o SQLite para la sintaxis (aunque SQL estándar suele funcionar)
                dialect = engine.dialect.name
                default_false = "FALSE" if dialect == "postgresql" else "0"
                conn.execute(text(f"ALTER TABLE turnos ADD COLUMN recordatorio_enviado BOOLEAN DEFAULT {default_false}"))
                conn.commit()
            logger.info("✅ Columna 'recordatorio_enviado' agregada.")

        if "recordatorio_fecha" not in columns:
            logger.info("⚠️ Columna 'recordatorio_fecha' faltante. Agregando...")
            with engine.connect() as conn:
                # TIMESTAMP works in PG. DATETIME in SQLite.
                # SQLAlchemy TEXT type handles dialect diffs usually but raw SQL needs care.
                # Try generic TIMESTAMP first.
                try:
                    conn.execute(text("ALTER TABLE turnos ADD COLUMN recordatorio_fecha TIMESTAMP"))
                except:
                     conn.execute(text("ALTER TABLE turnos ADD COLUMN recordatorio_fecha DATETIME"))
                conn.commit()
            logger.info("✅ Columna 'recordatorio_fecha' agregada.")
            
        if "recordatorio_usuario_id" not in columns:
            logger.info("⚠️ Columna 'recordatorio_usuario_id' faltante. Agregando...")
            with engine.connect() as conn:
                # FK reference syntax varies. Safer to add Int column first.
                conn.execute(text("ALTER TABLE turnos ADD COLUMN recordatorio_usuario_id INTEGER")) 
                # Adding constraints via raw SQL is risky across dialects without names. 
                # We skip FK constraint enforcement on DB level for this hotfix to avoid errors, 
                # logic is handled in app.
                conn.commit()
            logger.info("✅ Columna 'recordatorio_usuario_id' agregada.")

    # 2. Verificar tabla 'users'
    if inspector.has_table("users"):
        user_columns = [col["name"] for col in inspector.get_columns("users")]
        
        if "allowed_agendas" not in user_columns:
            logger.info("⚠️ Columna 'allowed_agendas' faltante en 'users'. Agregando...")
            with engine.connect() as conn:
                conn.execute(text("ALTER TABLE users ADD COLUMN allowed_agendas VARCHAR"))
                conn.commit()
            logger.info("✅ Columna 'allowed_agendas' agregada exitosamente.")

        if "matricula" not in user_columns:
            logger.info("⚠️ Columna 'matricula' faltante en 'users'. Agregando...")
            with engine.connect() as conn:
                conn.execute(text("ALTER TABLE users ADD COLUMN matricula VARCHAR"))
                conn.commit()
            logger.info("✅ Columna 'matricula' agregada exitosamente.")

        if "full_name" not in user_columns:
            logger.info("⚠️ Columna 'full_name' faltante en 'users'. Agregando...")
            with engine.connect() as conn:
                conn.execute(text("ALTER TABLE users ADD COLUMN full_name VARCHAR"))
                conn.commit()
            logger.info("✅ Columna 'full_name' agregada exitosamente.")

    # 3. Verificar tabla 'pacientes'
    if inspector.has_table("pacientes"):
        p_columns = [col["name"] for col in inspector.get_columns("pacientes")]
        if "nro_afiliado" not in p_columns:
            logger.info("⚠️ Columna 'nro_afiliado' faltante en 'pacientes'. Agregando...")
            with engine.connect() as conn:
                conn.execute(text("ALTER TABLE pacientes ADD COLUMN nro_afiliado VARCHAR"))
                conn.commit()
            logger.info("✅ Columna 'nro_afiliado' agregada.")

    # 4. Verificar tabla 'historia_clinica'
    if inspector.has_table("historia_clinica"):
        h_columns = [col["name"] for col in inspector.get_columns("historia_clinica")]
        fields = [
            "motivo_consulta", "antecedentes", "examen_clinico", 
            "plan_estudio", "diagnostico_diferencial", 
            "tratamiento", "evolucion"
        ]
        for f in fields:
            if f not in h_columns:
                logger.info(f"⚠️ Columna '{f}' faltante en 'historia_clinica'. Agregando...")
                with engine.connect() as conn:
                    # Usamos TEXT para postgres/sqlite compat
                    conn.execute(text(f"ALTER TABLE historia_clinica ADD COLUMN {f} TEXT")) 
                    conn.commit()
                logger.info(f"✅ Columna '{f}' agregada.")

        # P0 Columns: Estado, Audit, Signature
        p0_cols = {
            "estado": "VARCHAR DEFAULT 'BORRADOR'",
            "creado_por_id": "INTEGER",
            "fecha_creacion": "TIMESTAMP",
            "editado_por_id": "INTEGER",
            "fecha_edicion": "TIMESTAMP",
            "firmado_por_id": "INTEGER",
            "fecha_firma": "TIMESTAMP",
            "es_enmienda_de_id": "INTEGER"
        }

        dialect = engine.dialect.name
        
        for col_name, col_type in p0_cols.items():
            if col_name not in h_columns:
                logger.info(f"⚠️ Columna '{col_name}' faltante en 'historia_clinica'. Agregando...")
                with engine.connect() as conn:
                    # Adjust types if needed
                    final_type = col_type
                    if "TIMESTAMP" in col_type and dialect == "sqlite":
                        final_type = "DATETIME"
                    
                    conn.execute(text(f"ALTER TABLE historia_clinica ADD COLUMN {col_name} {final_type}"))
                    conn.commit()
                logger.info(f"✅ Columna '{col_name}' agregada.")

        # P1 Columns: Oncology
        p1_cols = {
            "ecog": "INTEGER",
            "tnm": "VARCHAR",
            "estadio": "VARCHAR",
            "toxicidad": "TEXT"
        }

        for col_name, col_type in p1_cols.items():
             if col_name not in h_columns:
                logger.info(f"⚠️ Columna '{col_name}' faltante en 'historia_clinica'. Agregando...")
                with engine.connect() as conn:
                    conn.execute(text(f"ALTER TABLE historia_clinica ADD COLUMN {col_name} {col_type}"))
                    conn.commit()
                logger.info(f"✅ Columna '{col_name}' agregada.")
