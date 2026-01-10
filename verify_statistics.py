from fastapi.testclient import TestClient
from main import app
from auth.jwt import create_access_token

client = TestClient(app)

def test_excel_feed():
    token = create_access_token(data={"sub": "test", "role": "ADMIN"})
    response = client.get(f"/estadisticas/excel_feed?token={token}")
    
    if response.status_code != 200:
        print(f"FAILED: Status {response.status_code}")
        print(response.text)
        return

    data = response.json()
    print(f"SUCCESS: Retrieved {len(data)} records")
    
    if len(data) > 0:
        first = data[0]
        print("Sample Record Keys:", first.keys())
        print("Sample Record:", first)
        
        required_fields = ["Referencia", "Paciente", "Edad", "Medico_Derivante", "Estado"]
        # Note: I used different keys in implementation, let's check what I actually used.
        # Implementation used: ID_Turno, Fecha, Hora, Paciente, DNI, Edad, Estado, Medico_Derivante...
        
        if "Edad" in first:
            print("✅ Field 'Edad' is present.")
        else:
            print(f"❌ Field 'Edad' is MISSING.")

if __name__ == "__main__":
    test_excel_feed()
