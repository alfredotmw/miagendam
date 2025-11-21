from sqlalchemy.orm import Session
from database import SessionLocal
from models.practica import Practica
from models.agenda import Agenda

def verify_data():
    db = SessionLocal()
    print("🔍 Verificando datos insertados...")

    # Verificar Prácticas
    practicas_esperadas = [
        "QUIMIOTERAPIA (SESION)",
        "CONSULTA ONCOLOGICA"
    ]
    for nombre in practicas_esperadas:
        p = db.query(Practica).filter_by(nombre=nombre).first()
        if p:
            print(f"✅ Práctica encontrada: {p.nombre} ({p.categoria})")
        else:
            print(f"❌ Práctica NO encontrada: {nombre}")

    # Verificar Agendas
    agendas_esperadas = [
        "QUIMIOTERAPIA SAN MARTIN",
        "CONSULTORIO DR. RUIZ FRANCHESCUTTI"
    ]
    for nombre in agendas_esperadas:
        a = db.query(Agenda).filter_by(nombre=nombre).first()
        if a:
            print(f"✅ Agenda encontrada: {a.nombre} (Tipo: {a.tipo})")
        else:
            print(f"❌ Agenda NO encontrada: {nombre}")

    db.close()

if __name__ == "__main__":
    verify_data()
