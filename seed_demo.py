# seed_demo.py
import requests
from datetime import date

BASE_URL = "http://127.0.0.1:8000"


def crear_admin():
    print("👤 Creando usuario administrador...")
    try:
        r = requests.post(f"{BASE_URL}/users/register", json={
            "username": "Alfredo",
            "password": "1234",
            "role": "ADMIN"
        })
        if r.status_code == 200:
            print("✅ Admin creado correctamente.")
        elif r.status_code == 400:
            print("⚠️ El usuario ya existe.")
        else:
            print(f"❌ Error al crear admin: {r.status_code} ({r.text})")
    except Exception as e:
        print(f"❌ Error de red: {e}")


def login_admin():
    print("\n🔐 Iniciando sesión como admin...")
    try:
        r = requests.post(f"{BASE_URL}/users/login", json={
            "username": "Alfredo",
            "password": "1234"
        })
        if r.status_code == 200:
            token = r.json()["access_token"]
            print("✅ Login correcto.")
            return {"Authorization": f"Bearer {token}"}
        else:
            print(f"❌ Error al loguear: {r.status_code} ({r.text})")
    except Exception as e:
        print(f"❌ Error de red: {e}")
    return None


def crear_agendas(headers):
    print("\n📅 Creando agendas médicas y de servicios...")
    agendas = [
        {"nombre": "Dr. Romilio Monzón", "tipo": "MEDICO", "slot_minutos": 15, "activo": True},
        {"nombre": "Dr. Fernandez Cespedes", "tipo": "MEDICO", "slot_minutos": 15, "activo": True},
        {"nombre": "Dra. Natalia Ayala", "tipo": "MEDICO", "slot_minutos": 15, "activo": True},
        {"nombre": "Tomografía y Radiografía", "tipo": "SERVICIO", "slot_minutos": 20, "activo": True},
        {"nombre": "PET", "tipo": "SERVICIO", "slot_minutos": 60, "activo": True},
        {"nombre": "Radioterapia SM", "tipo": "SERVICIO", "slot_minutos": 10, "activo": True},
        {"nombre": "Radioterapia CO", "tipo": "SERVICIO", "slot_minutos": 15, "activo": True},
        {"nombre": "Ecografías", "tipo": "SERVICIO", "slot_minutos": 15, "activo": True},
        {"nombre": "Cámara Gamma", "tipo": "SERVICIO", "slot_minutos": 30, "activo": True},
    ]

    for ag in agendas:
        r = requests.post(f"{BASE_URL}/agendas/", json=ag, headers=headers)
        if r.status_code == 200:
            print(f"✅ Agenda creada: {ag['nombre']}")
        elif r.status_code == 400:
            print(f"⚠️ Ya existe la agenda: {ag['nombre']}")
        else:
            print(f"❌ Error al crear {ag['nombre']}: {r.status_code} ({r.text})")


def crear_pacientes(headers):
    print("\n🧍 Creando pacientes de ejemplo...")
    pacientes = [
        {"dni": "38220123", "apellido_nombre": "Juan Pérez", "sexo": "M", "fecha_nacimiento": "1989-07-15", "celular": "3794123456"},
        {"dni": "29123123", "apellido_nombre": "María Gómez", "sexo": "F", "fecha_nacimiento": "1975-04-02", "celular": "3794789654"},
        {"dni": "40555111", "apellido_nombre": "Carlos Rodríguez", "sexo": "M", "fecha_nacimiento": "1992-11-23", "celular": "3794112233"},
    ]

    for p in pacientes:
        r = requests.post(f"{BASE_URL}/pacientes/", json=p, headers=headers)
        if r.status_code == 200:
            print(f"✅ Paciente cargado: {p['apellido_nombre']}")
        elif r.status_code == 400:
            print(f"⚠️ Paciente ya existente: {p['apellido_nombre']}")
        else:
            print(f"❌ Error al cargar {p['apellido_nombre']}: {r.status_code} ({r.text})")


def crear_turnos(headers):
    print("\n📆 Creando turnos de ejemplo...")
    hoy = str(date.today())

    turnos = [
        {"dni": "38220123", "fecha": hoy, "hora": "09:00:00", "duracion_minutos": 15, "realizado": False, "agenda_id": 1},
        {"dni": "29123123", "fecha": hoy, "hora": "09:15:00", "duracion_minutos": 15, "realizado": False, "agenda_id": 2},
        {"dni": "40555111", "fecha": hoy, "hora": "10:00:00", "duracion_minutos": 60, "realizado": False, "agenda_id": 5},
    ]

    for t in turnos:
        r = requests.post(f"{BASE_URL}/turnos/", json=t, headers=headers)
        if r.status_code == 200:
            print(f"✅ Turno creado: DNI {t['dni']} ({t['hora']})")
        else:
            print(f"⚠️ Error al crear turno de DNI {t['dni']}: {r.status_code} ({r.text})")


if __name__ == "__main__":
    print("🚀 Iniciando carga de datos demo...\n")

    crear_admin()
    headers = login_admin()
    if headers:
        crear_agendas(headers)
        crear_pacientes(headers)
        crear_turnos(headers)

    print("\n🎯 Carga completa.")
