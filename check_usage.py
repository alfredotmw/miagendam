from database import SessionLocal
from models.practica import Practica
from models.turno import Turno
from models.turno_practica import TurnoPractica

db = SessionLocal()

practices_to_check = [
    "RECETA", "CERTIFICADO", "CONSULTA", "CONTROL", 
    "CONSULTA GENERAL", "CONSULTA ONCOLOGICA", "CONSULTA PALIATIVOS"
]

print("--- Checking Usage in Turnos ---")
for p_name in practices_to_check:
    practice = db.query(Practica).filter(Practica.nombre == p_name).first()
    if practice:
        count = db.query(TurnoPractica).filter(TurnoPractica.practica_id == practice.id).count()
        print(f"'{p_name}': used in {count} turnos.")
    else:
        print(f"'{p_name}': Not found in DB.")

db.close()
