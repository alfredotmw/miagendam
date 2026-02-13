from datetime import datetime
from fastapi import HTTPException
from services.turno_service import validate_date_rules

def test_validation():
    print("Iniciando prueba de validación de domingos...")
    # Sunday
    domingo = datetime(2026, 2, 22) # Feb 22, 2026 is Sunday
    try:
        validate_date_rules(domingo)
        print("❌ FAIL: Domingo 22/02/2026 pasó la validación (Debería fallar)")
    except HTTPException as e:
        print(f"✅ SUCCESS: Domingo bloqueado correctamente. Mensaje: {e.detail}")
    except Exception as e:
        print(f"❌ FAIL: Excepción inesperada: {type(e).__name__}: {e}")

    # Monday
    lunes = datetime(2026, 2, 23)
    try:
        validate_date_rules(lunes)
        print("✅ SUCCESS: Lunes 23/02/2026 pasó la validación (Correcto)")
    except HTTPException as e:
        print(f"❌ FAIL: Lunes fue bloqueado incorrectamente: {e.detail}")

if __name__ == "__main__":
    test_validation()
