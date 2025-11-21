from sqlalchemy.orm import Session
from database import SessionLocal, engine, Base
from models.practica import Practica, CategoriaPractica
from models.agenda import Agenda
from models.user import User, UserRole

# Asegurar que las tablas existan (por si acaso)
Base.metadata.create_all(bind=engine)

def seed_full_data():
    db = SessionLocal()
    print("🚀 Iniciando carga de datos completa...")

    # 1. Cargar Nuevas Prácticas
    nuevas_practicas = {
        "QUIMIOTERAPIA": [
            "QUIMIOTERAPIA (SESION)",
            "QUIMIOTERAPIA (CONSULTA)"
        ],
        "CONSULTA_MEDICA": [
            "CONSULTA ONCOLOGICA",
            "CONSULTA GENERAL",
            "CONSULTA PALIATIVOS"
        ]
    }

    print("   ↳ Verificando Prácticas...")
    for categoria, lista_practicas in nuevas_practicas.items():
        for nombre in lista_practicas:
            if not db.query(Practica).filter_by(nombre=nombre).first():
                print(f"      + Creando Práctica: {nombre}")
                db.add(Practica(nombre=nombre, categoria=CategoriaPractica[categoria]))
    
    db.commit()

    # 2. Cargar Agendas de Servicios
    servicios = [
        {"nombre": "QUIMIOTERAPIA SAN MARTIN", "tipo": "QUIMIOTERAPIA"},
        {"nombre": "QUIMIOTERAPIA COLOMBIA", "tipo": "QUIMIOTERAPIA"},
        {"nombre": "RADIOTERAPIA SAN MARTIN", "tipo": "RADIOTERAPIA"},
        {"nombre": "RADIOTERAPIA COLOMBIA", "tipo": "RADIOTERAPIA"},
        {"nombre": "TOMOGRAFIAS Y RX", "tipo": "TOMOGRAFIA"}, # Asumiendo tipo principal
        {"nombre": "ECOGRAFIAS", "tipo": "ECOGRAFIA"},
        {"nombre": "CAMARA GAMMA", "tipo": "CAMARA_GAMMA"},
        {"nombre": "PET", "tipo": "PET"},
        {"nombre": "ELECTRO Y MAPEOS", "tipo": "ELECTRO_MAPEO"},
    ]

    print("   ↳ Verificando Agendas de Servicios...")
    for servicio in servicios:
        if not db.query(Agenda).filter_by(nombre=servicio["nombre"]).first():
            print(f"      + Creando Agenda Servicio: {servicio['nombre']}")
            db.add(Agenda(
                nombre=servicio["nombre"],
                tipo=servicio["tipo"],
                profesional=None
            ))
    
    db.commit()

    # 3. Cargar Agendas de Médicos
    medicos = [
        "Dr. Ruiz Franchescutti",
        "Dr. Fernandez Cespedes",
        "Dra. Natalia Ayala",
        "Dr. Lanari",
        "Dr. Monzòn",
        "Dr. Alinez",
        "Dra. Gutierrez",
        "Dra. Cabral Castella",
        "Dra. Serial",
        "Dra. Rewhald"
    ]

    print("   ↳ Verificando Agendas de Médicos...")
    for medico in medicos:
        nombre_agenda = f"CONSULTORIO {medico.upper()}"
        if not db.query(Agenda).filter_by(nombre=nombre_agenda).first():
            print(f"      + Creando Agenda Médico: {nombre_agenda}")
            db.add(Agenda(
                nombre=nombre_agenda,
                tipo="CONSULTA_MEDICA",
                profesional=medico
            ))

    db.commit()
    db.close()
    print("✅ Carga de datos finalizada exitosamente.")

if __name__ == "__main__":
    seed_full_data()
