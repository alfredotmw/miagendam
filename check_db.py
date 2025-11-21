# check_db.py
from pathlib import Path
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.exc import OperationalError, ProgrammingError
from database import SQLALCHEMY_DATABASE_URL  # debe existir en database.py

def main():
    print("🔎 Verificando base de datos...")
    print(f"🔗 URL de conexión: {SQLALCHEMY_DATABASE_URL}")

    # Si es SQLite, mostramos la ruta absoluta del archivo
    if SQLALCHEMY_DATABASE_URL.startswith("sqlite:///"):
        db_path = SQLALCHEMY_DATABASE_URL.replace("sqlite:///", "")
        abs_path = Path(db_path).resolve()
        print(f"📁 Archivo SQLite: {abs_path}  (existe: {abs_path.exists()})")

    engine = create_engine(SQLALCHEMY_DATABASE_URL, future=True)
    insp = inspect(engine)

    try:
        tables = insp.get_table_names()
    except OperationalError as e:
        print(f"❌ Error al inspeccionar tablas: {e}")
        return

    print("\n📋 Tablas en la base de datos:")
    if not tables:
        print("  (no se encontraron tablas)")
        print("\n💡 Siguientes pasos sugeridos:")
        print("  1) Verificá que 'database.py' apunte a la misma ruta usada por FastAPI.")
        print("  2) Corré las migraciones/creación de tablas (tu 'update_db.py' o Base.metadata.create_all).")
        print("  3) Asegurate de estar en la misma carpeta al ejecutar uvicorn y este script.")
        print("  4) Si usás múltiples bases (agenda.db, agendas.db), confirmá cuál es la activa.")
        return

    with engine.connect() as conn:
        for t in tables:
            print(f"\n— 🧱 {t}")
            # Columnas
            try:
                cols = insp.get_columns(t)
                col_str = ", ".join([f"{c['name']}({c.get('type')})" for c in cols])
                print(f"   • Columnas: {col_str or '(sin columnas?)'}")
            except Exception as e:
                print(f"   • Columnas: error al obtener columnas: {e}")

            # Primary Key
            try:
                pk = insp.get_pk_constraint(t).get("constrained_columns", [])
                print(f"   • PK: {pk or '(sin PK)'}")
            except Exception as e:
                print(f"   • PK: error al obtener PK: {e}")

            # Foreign Keys
            try:
                fks = insp.get_foreign_keys(t)
                if fks:
                    fk_strs = []
                    for fk in fks:
                        cols = ", ".join(fk.get("constrained_columns", []))
                        ref = fk.get("referred_table", "?")
                        ref_cols = ", ".join(fk.get("referred_columns", []))
                        fk_strs.append(f"{cols} -> {ref}({ref_cols})")
                    print(f"   • FKs: { '; '.join(fk_strs) }")
                else:
                    print("   • FKs: (sin FKs)")
            except Exception as e:
                print(f"   • FKs: error al obtener FKs: {e}")

            # Conteo de filas
            try:
                result = conn.execute(text(f"SELECT COUNT(*) FROM {t}"))
                count = result.scalar_one()
                print(f"   • Filas: {count}")
            except (OperationalError, ProgrammingError) as e:
                print(f"   • Filas: error al contar filas: {e}")

    print("\n✅ Verificación completa.")

if __name__ == "__main__":
    main()
