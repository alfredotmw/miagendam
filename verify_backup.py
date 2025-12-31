import requests
import json
import time
import subprocess
import sys
import uvicorn
from multiprocessing import Process

# Configuration
BASE_URL = "http://localhost:8001" # Using 8001 to avoid conflict with potential running dev server

def verify_backup():
    print("🚀 Iniciando verificación de Backup (Live Server)...")
    
    # 1. Login as Alfredo (Admin)
    print("🔑 Iniciando sesión como Admin...")
    login_data = {"username": "Alfredo", "password": "1234"}
    
    # Try form-encoded first (standard OAuth2)
    try:
        response = requests.post(f"{BASE_URL}/token", data=login_data)
        if response.status_code != 200:
             # Try JSON endpoint if different
             response = requests.post(f"{BASE_URL}/users/login", data=login_data)
    except requests.exceptions.ConnectionError:
        print("❌ No se pudo conectar al servidor. Asegúrate de que esté corriendo.")
        return False

    if response.status_code != 200:
        # Fallback to json if data failed
        response = requests.post(f"{BASE_URL}/users/login", json=login_data)
        
    if response.status_code != 200:
        print(f"❌ Login falló: {response.status_code} - {response.text}")
        return False
        
    # Get token - adapt to key
    data_json = response.json()
    token = data_json.get("access_token")
    if not token:
        print("❌ No se recibió token")
        return False
    
    print("✅ Login exitoso.")
    
    # 2. Request Backup
    print("📥 Solicitando backup...")
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/backup/download", headers=headers)
    
    if response.status_code != 200:
        print(f"❌ Error al descargar backup: {response.status_code} - {response.text}")
        return False
    
    # 3. Verify Content
    content = response.content
    try:
        data = json.loads(content)
        print("✅ Backup descargado y es JSON válido.")
        
        # Check keys
        keys = ["pacientes", "turnos", "historia_clinica", "users", "agendas"]
        missing = [k for k in keys if k not in data]
        if missing:
            print(f"⚠️ Faltan claves en el backup: {missing}")
        else:
            print(f"✅ Estructura correcta. Pacientes: {len(data['pacientes'])}, Turnos: {len(data['turnos'])}")
            
        # Verify specific content if possible
        if len(data['users']) > 0:
            print(f"   Usuarios encontrados: {len(data['users'])}")
            
    except json.JSONDecodeError:
        print(f"❌ El contenido no es JSON válido. Inicio: {content[:100]}")
        return False
        
    return True

if __name__ == "__main__":
    # Ensure server is running or start it?
    # For this script, we assume we will start the server externally or in a separate thread.
    # But to make it self-contained, let's try to ping, if not up, fail.
    # The caller (agent) should start the server.
    
    try:
        if verify_backup():
            print("\n🎉 VERIFICACIÓN EXITOSA: El sistema de backup funciona correctamente.")
        else:
            print("\n❌ VERIFICACIÓN FALLIDA.")
            exit(1)
    except Exception as e:
        print(f"\n❌ EXCEPCIÓN: {e}")
        exit(1)
