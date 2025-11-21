from database import SessionLocal
from models.obra_social import ObraSocial

# Lista de obras sociales
obras = [
    "IOSCOR",
    "PAMI",
    "OSECAC",
    "MINISTERIO DE SALUD PUBLICA CORRIENTES",
    "UPCN",
    "OSDE",
    "MEDIFE",
    "SWISS MEDICAL",
    "IOSFA",
    "GLOBAL EMPRESARIA",
    "BOREAL",
    "BRAMED",
    "PAMI CHACO",
    "OSPECON",
    "OSACRA",
    "OSPSA",
    "LUZ Y FUERZA",
    "AGUA Y ENERGIA",
    "INSSSEP",
    "UNNE",
    "PODER JUDICIAL",
    "POLICIA FEDERAL",
    "PARTICULAR",
]

# Abrir sesión
db = SessionLocal()

# Insertar solo las que no existan
for nombre in obras:
    existente = db.query(ObraSocial).filter(ObraSocial.nombre == nombre).first()
    if not existente:
        nueva = ObraSocial(nombre=nombre)
        db.add(nueva)

db.commit()
db.close()

print("✅ Obras sociales cargadas correctamente.")
