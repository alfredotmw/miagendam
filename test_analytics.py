from fastapi.testclient import TestClient
from main import app
import pandas as pd
import io

client = TestClient(app)

def test_analytics():
    print("📊 Probando Endpoints de Analítica...")

    # 1. Probar Live Data (JSON para Power Query)
    print("1️⃣  Probando /analytics/live_data...")
    response = client.get("/analytics/live_data")
    assert response.status_code == 200
    data = response.json()
    print(f"    ✅ Status 200 OK. Registros obtenidos: {len(data)}")
    if len(data) > 0:
        print(f"    Ejemplo de registro: {data[0]}")
    else:
        print("    ⚠️ No hay datos para mostrar (base vacía o sin turnos).")

    # 2. Probar Descarga Excel
    print("\n2️⃣  Probando /analytics/download...")
    response = client.get("/analytics/download")
    assert response.status_code == 200
    assert "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" in response.headers["content-type"]
    
    # Verificar que es un Excel válido
    try:
        df = pd.read_excel(io.BytesIO(response.content))
        print(f"    ✅ Excel generado correctamente. Filas: {len(df)}")
    except Exception as e:
        print(f"    ❌ Error al leer el Excel generado: {e}")

if __name__ == "__main__":
    test_analytics()
