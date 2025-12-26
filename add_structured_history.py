from database import engine
from sqlalchemy import text

def migrate_structure():
    with engine.connect() as conn:
        try:
            # 1. Add nro_afiliado to Pacientes
            try:
                conn.execute(text("ALTER TABLE pacientes ADD COLUMN nro_afiliado VARCHAR"))
                print("✅ [Paciente] Column 'nro_afiliado' added.")
            except Exception as e:
                print(f"⚠️ [Paciente] Column 'nro_afiliado' likely exists: {e}")

            # 2. Add columns to HistoriaClinica
            fields = [
                "motivo_consulta", "antecedentes", "examen_clinico", 
                "plan_estudio", "diagnostico_diferencial", 
                "tratamiento", "evolucion"
            ]
            
            for f in fields:
                try:
                    conn.execute(text(f"ALTER TABLE historia_clinica ADD COLUMN {f} TEXT"))
                    print(f"✅ [Historia] Column '{f}' added.")
                except Exception as e:
                     print(f"⚠️ [Historia] Column '{f}' likely exists: {e}")
            
            # 3. Make 'texto' nullable if it wasn't (trickier in raw sql, skipping alter column for simplicity as adding new ones is safe)
            # We will just treat 'texto' as optional in app logic.
                
            conn.commit()
            print("🚀 Structured History Migration completed.")
        except Exception as e:
            print(f"❌ Migration failed: {e}")

if __name__ == "__main__":
    migrate_structure()
