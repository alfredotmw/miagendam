import logging
from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine

logger = logging.getLogger(__name__)

def check_and_migrate_db(engine: Engine):
    """
    Verifica si faltan columnas en la base de datos y las agrega.
    Esto es una migración simple 'manual' para evitar usar Alembic por ahora.
    """
    try:
        if engine.dialect.name == "postgresql":
            with engine.connect() as conn:
                conn.execute(text("SET lock_timeout = '5s';"))
                conn.commit()
    except Exception as e:
        logger.warning(f"No se pudo establecer lock_timeout: {e}")
        
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

        # Chequear columna 'observaciones'
        if "observaciones" not in columns:
            logger.info("⚠️ Columna 'observaciones' faltante en 'turnos'. Agregando...")
            with engine.connect() as conn:
                conn.execute(text("ALTER TABLE turnos ADD COLUMN observaciones TEXT"))
                conn.commit()
            logger.info("✅ Columna 'observaciones' agregada exitosamente.")
        else:
            logger.info("✅ Columna 'observaciones' ya existe en 'turnos'.")

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

        if "especialidad" not in user_columns:
            logger.info("⚠️ Columna 'especialidad' faltante en 'users'. Agregando...")
            with engine.connect() as conn:
                conn.execute(text("ALTER TABLE users ADD COLUMN especialidad VARCHAR"))
                conn.commit()
            logger.info("✅ Columna 'especialidad' agregada exitosamente.")

    # 3. Verificar tabla 'pacientes'
    if inspector.has_table("pacientes"):
        p_columns = [col["name"] for col in inspector.get_columns("pacientes")]
        if "nro_afiliado" not in p_columns:
            logger.info("⚠️ Columna 'nro_afiliado' faltante en 'pacientes'. Agregando...")
            with engine.connect() as conn:
                conn.execute(text("ALTER TABLE pacientes ADD COLUMN nro_afiliado VARCHAR"))
                conn.commit()
            logger.info("✅ Columna 'nro_afiliado' agregada.")
            
            with engine.connect() as conn:
                conn.execute(text("ALTER TABLE pacientes ADD COLUMN medico_derivante_id INTEGER REFERENCES medicos_derivantes(id)"))
                conn.commit()
            logger.info("✅ Columna 'medico_derivante_id' agregada.")

        if "patologia" not in p_columns:
            logger.info("⚠️ Columna 'patologia' faltante en 'pacientes'. Agregando...")
            with engine.connect() as conn:
                conn.execute(text("ALTER TABLE pacientes ADD COLUMN patologia VARCHAR"))
                conn.commit()
            logger.info("✅ Columna 'patologia' agregada a pacientes.")

    # 4. Verificar tabla 'historia_clinica'
    if inspector.has_table("historia_clinica"):
        h_columns = [col["name"] for col in inspector.get_columns("historia_clinica")]
        fields = [
            "motivo_consulta", "antecedentes", "examen_clinico", 
            "plan_estudio", "diagnostico_diferencial", 
            "tratamiento", "evolucion", "patologia"
        ]
        for f in fields:
            if f not in h_columns:
                logger.info(f"⚠️ Columna '{f}' faltante en 'historia_clinica'. Agregando...")
                with engine.connect() as conn:
                    # Usamos TEXT para postgres/sqlite compat
                    conn.execute(text(f"ALTER TABLE historia_clinica ADD COLUMN {f} TEXT")) 
                    conn.commit()
                logger.info(f"✅ Columna '{f}' agregada.")

        if "especialidad_medico" not in h_columns:
            logger.info("⚠️ Columna 'especialidad_medico' faltante en 'historia_clinica'. Agregando...")
            with engine.connect() as conn:
                conn.execute(text("ALTER TABLE historia_clinica ADD COLUMN especialidad_medico VARCHAR"))
                conn.commit()
            logger.info("✅ Columna 'especialidad_medico' agregada.")

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

        # P2 Columns: Structured Evolution Redesign
        p2_cols = {
            "examen_fisico_estructurado": "JSON",
            "indicaciones": "JSON",
            "proximo_control": "DATE",
            "pautas_alarma": "TEXT",
            "situacion_cierre": "VARCHAR"
        }

        for col_name, col_type in p2_cols.items():
            if col_name not in h_columns:
                logger.info(f"⚠️ Columna '{col_name}' faltante en 'historia_clinica'. Agregando...")
                with engine.connect() as conn:
                    # JSON type handling might vary slightly if SQLite vs Postgres
                    # but SQLAlchemy text execute handles basic JSON/TEXT fallback well.
                    # Use TEXT for JSON if sqlite, else JSON for PG.
                    resolved_type = col_type
                    if col_type == "JSON" and dialect == "sqlite":
                        resolved_type = "TEXT"
                    
                    conn.execute(text(f"ALTER TABLE historia_clinica ADD COLUMN {col_name} {resolved_type}"))
                    conn.commit()
                logger.info(f"✅ Columna '{col_name}' agregada.")

        # Automation Column: Radiotherapy
        if "requiere_radioterapia" not in h_columns:
            logger.info("⚠️ Columna 'requiere_radioterapia' faltante en 'historia_clinica'. Agregando...")
            with engine.connect() as conn:
                dialect = engine.dialect.name
                default_false = "FALSE" if dialect == "postgresql" else "0"
                col_type = "BOOLEAN" if dialect == "postgresql" else "INTEGER"
                conn.execute(text(f"ALTER TABLE historia_clinica ADD COLUMN requiere_radioterapia {col_type} DEFAULT {default_false}"))
                conn.commit()
            logger.info("✅ Columna 'requiere_radioterapia' agregada.")

        # 🟢 NEW: Column 'tipo_evolucion' (Fix 500 Global Error on Backup/History)
        if "tipo_evolucion" not in h_columns:
            logger.info("⚠️ Columna 'tipo_evolucion' faltante en 'historia_clinica'. Agregando...")
            with engine.connect() as conn:
                conn.execute(text("ALTER TABLE historia_clinica ADD COLUMN tipo_evolucion VARCHAR"))
                conn.commit()
            logger.info("✅ Columna 'tipo_evolucion' agregada.")

    # 5. Verificar tabla 'agendas'
    if inspector.has_table("agendas"):
        a_columns = [col["name"] for col in inspector.get_columns("agendas")]
        dialect = engine.dialect.name
        
        if "slot_minutos" not in a_columns:
            logger.info("⚠️ Columna 'slot_minutos' faltante en 'agendas'. Agregando...")
            with engine.connect() as conn:
                conn.execute(text("ALTER TABLE agendas ADD COLUMN slot_minutos INTEGER DEFAULT 20"))
                conn.commit()
            logger.info("✅ Columna 'slot_minutos' agregada.")
            
        if "activo" not in a_columns:
            logger.info("⚠️ Columna 'activo' faltante en 'agendas'. Agregando...")
            with engine.connect() as conn:
                # Default true/1
                default_true = "TRUE" if dialect == "postgresql" else "1"
                # Use INTEGER for boolean compat if desired, or BOOLEAN in PG
                col_type = "BOOLEAN" if dialect == "postgresql" else "INTEGER"
                conn.execute(text(f"ALTER TABLE agendas ADD COLUMN activo {col_type} DEFAULT {default_true}"))
                conn.commit()
            logger.info("✅ Columna 'activo' agregada.")
            
    # 6. Verificar tabla 'seguimiento_radioterapia'
    if inspector.has_table("seguimiento_radioterapia"):
        rt_columns = [col["name"] for col in inspector.get_columns("seguimiento_radioterapia")]
        
        if "sede" not in rt_columns:
            logger.info("⚠️ Columna 'sede' faltante en 'seguimiento_radioterapia'. Agregando...")
            with engine.connect() as conn:
                conn.execute(text("ALTER TABLE seguimiento_radioterapia ADD COLUMN sede VARCHAR"))
                conn.commit()
            logger.info("✅ Columna 'sede' agregada.")
            
        if "tipo_tecnica" not in rt_columns:
            logger.info("⚠️ Columna 'tipo_tecnica' faltante en 'seguimiento_radioterapia'. Agregando...")
            with engine.connect() as conn:
                conn.execute(text("ALTER TABLE seguimiento_radioterapia ADD COLUMN tipo_tecnica VARCHAR"))
                conn.commit()
            logger.info("✅ Columna 'tipo_tecnica' agregada.")

    # 7. DATA INTEGRITY BLINDAGE (00:00 turns and Duplicates)
    if inspector.has_table("turnos"):
        with engine.connect() as conn:
            # A. Delete 00:00:00 turns
            logger.info("🧹 Migración: Limpiando turnos fantasma (00:00)...")
            res = conn.execute(text("DELETE FROM turnos WHERE hora LIKE '00:00%'"))
            if res.rowcount > 0:
                logger.info(f"[SUCCESS] Se eliminaron {res.rowcount} turnos con hora inválida.")
            
            # B. Delete true duplicates (same agenda/patient/practice/day)
            # This logic is complex for raw SQL in migration. We'll stick to basic cleanup 
            # or just rely on the UNIQUE index creation which will fail if not clean.
            # Best: Clean before index.
            
            logger.info("[CLEANUP] Migración: Limpiando turnos duplicados en Quimioterapia (OMITIDO POR TIMEOUT)...")
            # --- ELIMINADO EL CÓDIGO DE LIMPIEZA DE DUPLICADOS O(N^2) ---
            # La limpieza se hizo el 27 de febrero y el índice único ya previene duplicados.
            # Ejecutar esta consulta en cada inicio causaba un timeout de más de 30 segundos
            # en Render al crecer la base de datos.
            
            # C. Apply UNIQUE Index (Blindaje)
            logger.info("🛡️ Aplicando Blindaje: Índice Único (Agenda, Paciente, Fecha)...")
            try:
                # SQLite and Postgres handle this similarly. 
                # Name it idx_unique_turno_integrity
                conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS idx_unique_turno_integrity ON turnos(agenda_id, paciente_id, fecha)"))
                conn.commit()
                logger.info("✅ Índice único de integridad aplicado.")
            except Exception as e:
                logger.warning(f"⚠️ No se pudo aplicar el índice único (posibles duplicados remanentes): {e}")

            # D. Migrate historical pathologies from turnos to pacientes
            logger.info("🔄 Migración: Sincronizando patologías históricas de turnos a pacientes...")
            try:
                query_mig = """
                UPDATE pacientes
                SET patologia = (
                    SELECT t.patologia
                    FROM turnos t
                    WHERE t.paciente_id = pacientes.id
                      AND t.patologia IS NOT NULL
                      AND t.patologia != ''
                    ORDER BY t.fecha DESC
                    LIMIT 1
                )
                WHERE (pacientes.patologia IS NULL OR pacientes.patologia = '');
                """
                res = conn.execute(text(query_mig))
                conn.commit()
                if res.rowcount > 0:
                    logger.info(f"✅ Se sincronizaron {res.rowcount} patologías de turnos a pacientes.")
                else:
                    logger.info("ℹ️ No se requirió sincronización de patologías o ya estaban actualizadas.")
            except Exception as e:
                logger.warning(f"⚠️ No se pudo realizar la sincronización de patologías: {e}")

            conn.commit()
