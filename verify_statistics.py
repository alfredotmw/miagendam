from fastapi.testclient import TestClient
from main import app
from auth.jwt import create_access_token

client = TestClient(app)

def test_dashboard_logic():
    # Use a mock token if needed, or just rely on dependency overrides if possible. 
    # For this script we try to use a real token or bypass authentication if running locally against a test DB.
    # However, 'client' bypasses HTTP server auth but runs dependencies.
    # Let's try to get a token first.
    
    token = create_access_token(data={"sub": "test", "role": "ADMIN"})
    
    # Test Dashboard Endpoint
    response = client.get(f"/analytics/dashboard?token={token}") # Endpoint changed from /estadisticas to /analytics
    
    if response.status_code != 200:
        print(f"FAILED: Status {response.status_code}")
        print(response.text)
        return

    data = response.json()
    print("SUCCESS: Dashboard Data Retrieved")
    
    if "services_data" in data:
        services = [s["service"] for s in data["services_data"]]
        print("Found Services:", services)
        
        # Check for new keys
        if "RADIOTERAPIA SM" in services or "RADIOTERAPIA COL" in services:
             print("✅ 'RADIOTERAPIA SM/COL' split detected.")
        else:
             print("⚠️ 'RADIOTERAPIA SM/COL' NOT found (Maybe no data in DB for these?)")
             
        if "TOMOGRAFIA" in services and "RADIOGRAFIA" in services:
             print("✅ Both 'TOMOGRAFIA' and 'RADIOGRAFIA' detected.")
    else:
        print("❌ 'services_data' key missing.")

if __name__ == "__main__":
    test_dashboard_logic()
