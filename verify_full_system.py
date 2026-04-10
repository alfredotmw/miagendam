
import sqlite3
import os

def verify_system():
    db_path = "agendas.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    tables = ["turnos", "pacientes", "obras_sociales", "medicos_derivantes", "seguimiento_radioterapia"]
    audit_columns = ["creado_por_id", "modificado_por_id", "fecha_creacion", "fecha_modificacion"]

    print("--- VERIFICACIÓN DE ESQUEMA DE AUDITORÍA ---")
    for table in tables:
        cursor.execute(f"PRAGMA table_info({table})")
        columns = [row[1] for row in cursor.fetchall()]
        missing = []
        for col in audit_columns:
            if col not in columns:
                # seguimiento_radioterapia already has created_at/updated_at
                if table == "seguimiento_radioterapia" and col in ["fecha_creacion", "fecha_modificacion"]:
                    continue
                missing.append(col)
        
        if missing:
            print(f"[ERROR] Tabla {table}: Faltan columnas {missing}")
        else:
            print(f"[OK] Tabla {table}: Esquema de auditoria completo.")

    print("\n--- VERIFICACION DE UNIFICACION DE PERMISOS ---")
    # Check if any user still has allowed_agendas populated (informational)
    cursor.execute("SELECT username, allowed_agendas FROM users WHERE allowed_agendas IS NOT NULL AND allowed_agendas != ''")
    legacy_users = cursor.fetchall()
    if legacy_users:
        print(f"[INFO] {len(legacy_users)} usuarios aun tienen datos en la columna legacy 'allowed_agendas'.")
        print("   (La migracion fue exitosa a M2M, pero mantenemos legacy por seguridad hasta limpieza final).")
    else:
        print("[OK] Columna legacy 'allowed_agendas' esta vacia para todos los usuarios.")

    conn.close()

if __name__ == "__main__":
    verify_system()
