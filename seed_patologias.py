from database import SessionLocal, engine, Base
from models.patologia import Patologia

# Ensure table exists
Base.metadata.create_all(bind=engine)

INITIAL_LIST = [
    "Carcinoma de Mama",
    "Carcinoma de Pulmón (No Células Pequeñas)",
    "Carcinoma de Pulmón (Células Pequeñas)",
    "Cáncer de Próstata",
    "Cáncer Colorrectal",
    "Cáncer de Colon",
    "Cáncer de Recto",
    "Cáncer de Páncreas",
    "Carcinoma Hepatocelular (Hígado)",
    "Cáncer Gástrico (Estómago)",
    "Cáncer de Esófago",
    "Cáncer de Ovario",
    "Cáncer de Endometrio",
    "Cáncer de Cuello Uterino",
    "Cáncer de Riñón (Carcinoma de Células Renales)",
    "Cáncer de Vejiga",
    "Melanoma",
    "Carcinoma Basocelular",
    "Carcinoma Espinocelular",
    "Linfoma Hodgkin",
    "Linfoma No Hodgkin",
    "Mieloma Múltiple",
    "Leucemia Mieloide Aguda",
    "Leucemia Linfoide Aguda",
    "Leucemia Mieloide Crónica",
    "Leucemia Linfoide Crónica",
    "Glioblastoma Multiforme",
    "Astrocitoma",
    "Meningioma",
    "Sarcoma de Tejidos Blandos",
    "Osteosarcoma",
    "Cáncer de Tiroides",
    "Cáncer de Cabeza y Cuello",
    "Tumor Neuroendocrino",
    "Cáncer de Testículo",
    # Metastasis
    "Metástasis de Cáncer de Mama",
    "Metástasis de Cáncer de Pulmón",
    "Metástasis de Cáncer de Próstata",
    "Metástasis de Cáncer de Colon",
    "Metástasis de Cáncer de Recto",
    "Metástasis de Melanoma",
    "Metástasis de Cáncer Renal",
    "Metástasis de Cáncer de Vejiga",
    "Metástasis de Sarcoma",
    "Metástasis Óseas (Origen Desconocido)",
    "Metástasis Cerebrales (Origen Desconocido)",
    "Metástasis Hepáticas (Origen Desconocido)",
    "Metástasis Pulmonares (Origen Desconocido)",
    "Carcinomatosis Peritoneal"
]

def seed():
    db = SessionLocal()
    try:
        count = 0
        for name in INITIAL_LIST:
            exists = db.query(Patologia).filter(Patologia.nombre == name).first()
            if not exists:
                db.add(Patologia(nombre=name))
                count += 1
        db.commit()
        print(f"Seeded {count} new pathologies.")
    finally:
        db.close()

if __name__ == "__main__":
    seed()
