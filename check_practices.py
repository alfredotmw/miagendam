from database import SessionLocal
from models.practica import Practica, CategoriaPractica

db = SessionLocal()

print("--- Practices in CONSULTA_MEDICA ---")
practices = db.query(Practica).filter(Practica.categoria == CategoriaPractica.CONSULTA_MEDICA).all()
for p in practices:
    print(f"- {p.nombre}")

print("\n--- Searching for 'Receta/certificado' (any category) ---")
receta = db.query(Practica).filter(Practica.nombre.ilike("%Receta%")).all()
for p in receta:
    print(f"Found: {p.nombre} ({p.categoria})")

db.close()
