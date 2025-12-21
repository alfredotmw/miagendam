
from sqlalchemy.orm import Session
from database import SessionLocal
from models.practica import Practica, CategoriaPractica

def add_new_practices():
    db = SessionLocal()
    print("🔎 Verificando prácticas de consultorio...")

    new_practices = [
        "CONSULTA DE 1RA VEZ",
        "CONSULTA DE CONTROL"
    ]

    count = 0
    for nombre in new_practices:
        exists = db.query(Practica).filter_by(nombre=nombre).first()
        if not exists:
            print(f"➕ Agregando: {nombre}")
            db.add(Practica(nombre=nombre, categoria=CategoriaPractica.CONSULTA_MEDICA))
            count += 1
        else:
            print(f"✅ Ya existe: {nombre}")

    if count > 0:
        db.commit()
        print(f"🎉 Se agregaron {count} nuevas prácticas.")
    else:
        print("👌 No se requirieron cambios.")

    db.close()

if __name__ == "__main__":
    add_new_practices()
