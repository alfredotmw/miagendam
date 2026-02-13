import requests
from datetime import datetime, date

# Config
BASE_URL = "http://localhost:8000"
# Asumimos que tienes un usuario y un paciente creados. 
# Si no, esto es una prueba unitaria del endpoint mockeando la DB o usándola directo.
# Mejor testear el endpoint si el servidor corre, o testear la función si tengo acceso a DB local.
# Dado que tengo acceso al código, haré un script que use la Session local para simular la petición.

from database import SessionLocal
from models.turno import Turno
from models.paciente import Paciente
from schemas.check_duplicates import CheckDuplicates
from routers.turnos import verificar_duplicados

def test_duplicate_check():
    db = SessionLocal()
    try:
        # 1. Buscar un paciente que ya tenga turnos
        print("Buscando paciente con turnos...")
        turno_existente = db.query(Turno).filter(Turno.estado != "CANCELADO").first()
        
        if not turno_existente:
            print("⚠️ No hay turnos en la base de datos para probar. Creando uno temporal...")
            # (Omitido para no ensuciar, mejor buscar otro o fallar graceful)
            return

        paciente_id = turno_existente.paciente_id
        fecha_existente = turno_existente.fecha.date()
        fecha_nueva_random = date(2028, 1, 1) # Futuro lejano

        print(f"Paciente ID: {paciente_id}")
        print(f"Fecha con turno: {fecha_existente}")
        
        # 2. Probar Check con fecha existente (Debe alertar)
        print("\n--- Test 1: Fecha Duplicada ---")
        check_1 = CheckDuplicates(
            paciente_id=paciente_id,
            fechas=[fecha_existente, fecha_nueva_random]
        )
        res_1 = verificar_duplicados(check_1, db, current_user={})
        print(f"Resultado: {res_1}")
        
        if res_1.get("status") == "alerta" and str(fecha_existente.strftime("%d/%m/%Y")) in res_1.get("mensaje"):
            print("✅ SUCCESS: Detectó el duplicado correctamente.")
        else:
            print("❌ FAIL: No detectó el duplicado.")

        # 3. Probar Check con fechas limpias (Debe dar OK)
        print("\n--- Test 2: Fechas Limpias ---")
        check_2 = CheckDuplicates(
            paciente_id=paciente_id,
            fechas=[fecha_nueva_random]
        )
        res_2 = verificar_duplicados(check_2, db, current_user={})
        print(f"Resultado: {res_2}")
        
        if res_2.get("status") == "ok":
             print("✅ SUCCESS: Status OK para fechas sin turno.")
        else:
             print("❌ FAIL: Dio alerta falso positivo.")

    except Exception as e:
        print(f"❌ ERROR: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    test_duplicate_check()
