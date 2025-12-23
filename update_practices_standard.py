from sqlalchemy.orm import Session
from database import SessionLocal
from models.practica import Practica, CategoriaPractica

def standardize_practices():
    db = SessionLocal()
    print("🚀 Starting Practice Standardization...")

    # 1. Practices to be REMOVED (Old ones)
    to_remove = [
        "CONSULTA", 
        "CONSULTA GENERAL", 
        "CONSULTA ONCOLOGICA", 
        "CONSULTA PALIATIVOS", 
        "RECETA", 
        "CERTIFICADO", 
        "CONTROL"
    ]

    print("\n🗑️  Removing deprecated practices...")
    for name in to_remove:
        p = db.query(Practica).filter(Practica.nombre == name).first()
        if p:
            print(f"   - Deleting: {name}")
            db.delete(p)
        else:
            print(f"   - Not found (already deleted?): {name}")

    # 2. Practices to be ADDED/ENSURED (Standard ones)
    standard_practices = [
        "CONSULTA DE 1RA VEZ",
        "CONSULTA DE CONTROL",
        "RECETA/CERTIFICADO" # Merged one
    ]

    print("\n✨ Ensuring standard practices exist...")
    for name in standard_practices:
        p = db.query(Practica).filter(Practica.nombre == name).first()
        if not p:
            print(f"   + Creating: {name}")
            new_p = Practica(nombre=name, categoria=CategoriaPractica.CONSULTA_MEDICA)
            db.add(new_p)
        else:
            print(f"   ✓ Exists: {name} (Category: {p.categoria})")

    db.commit()
    db.close()
    print("\n✅ Standardization Complete.")

if __name__ == "__main__":
    standardize_practices()
