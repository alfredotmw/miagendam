from sqlalchemy.orm import Session
from database import SessionLocal
from models.obra_social import ObraSocial
from models.practica import Practica, CategoriaPractica


from models.user import User, UserRole
import bcrypt

def seed_users(db: Session):
    if not db.query(User).filter_by(username="Alfredo").first():
        print("👤 Creando usuario administrador 'Alfredo'...")
        hashed_password = bcrypt.hashpw("1234".encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        admin = User(username="Alfredo", password=hashed_password, role=UserRole.ADMIN)
        db.add(admin)
        db.commit()

def seed_obras_sociales(db: Session):
    obras = [
        "IOSCOR", "PAMI", "OSECAC", "MINISTERIO DE SALUD PUBLICA CORRIENTES",
        "UPCN", "OSDE", "MEDIFE", "SWISS MEDICAL", "IOSFA", "GLOBAL EMPRESARIA",
        "BOREAL", "BRAMED", "PAMI CHACO", "OSPECON", "OSACRA", "OSPSA",
        "LUZ Y FUERZA", "AGUA Y ENERGIA", "INSSSEP", "UNNE", "PODER JUDICIAL",
        "POLICIA FEDERAL", "PARTICULAR"
    ]

    for nombre in obras:
        if not db.query(ObraSocial).filter_by(nombre=nombre).first():
            db.add(ObraSocial(nombre=nombre))

    db.commit()


def seed_practicas(db: Session):
    categorias = {
        "TOMOGRAFIA": [
            "TAC DE CEREBRO",
            "TAC DE CEREBRO CON CONTRASTE",
            "TAC DE TORAX",
            "TAC DE TORAX CON CONTRASTE",
            "TAC COMPLETA DE ABDOMEN",
            "TAC COMPLETA DE ABDOMEN CON CONTRASTE",
            "TAC DE PELVIS",
            "TAC DE PELVIS CON CONTRASTE",
            "TAC DE OTROS ORGANOS Y REGIONES",
            "TAC DE CUELLO",
        ],
        "RADIOGRAFIA": [
            "RX DE TORAX",
            "RX DE COLUMNA CERVICAL",
            "RX DE COLUMNA DORSAL",
            "RX DE COLUMNA LUMBAR",
            "RX DE HOMBRO",
            "RX DE CODO",
            "RX DE MUÑECA",
            "RX DE MANO",
            "RX DE PELVIS",
            "RX DE CADERA",
            "RX DE RODILLA",
            "RX DE TOBILLO",
            "RX DE PIE",
            "RX DE CRANEO",
            "RX DE ABDOMEN SIMPLE",
            "RX DENTAL (PERIAPICAL / BITEWING)",
            "RX ORTOPANTOMOGRAFIA (PANORAMICA)"
        ],
        "ECOGRAFIA": [
            "ECOGRAFIA ABDOMINAL",
            "ECOGRAFIA PELVICA (GINECOLOGICA)",
            "ECOGRAFIA OBSTETRICA",
            "ECOGRAFIA MAMARIA",
            "ECOGRAFIA TIROIDEA",
            "ECOGRAFIA RENAL",
            "ECOGRAFIA VESICAL",
            "ECOGRAFIA PROSTATICA (TRANSRECTAL)",
            "ECOGRAFIA TESTICULAR",
            "ECOGRAFIA MUSCULOESQUELETICA",
            "ECOGRAFIA DOPPLER (VASCULAR)",
            "ECOCARDIOGRAMA",
            "ECOGRAFIA TRANSVAGINAL"
        ],
        "PET": [
            "PET CON FDG",
            "PET CON COLINA",
            "PET CON PSMA",
        ],
        "ELECTRO_MAPEO": [
            "EEG",
            "MAPEO CEREBRAL",
        ],
        "RADIOTERAPIA": [
            "RT 3D",
            "IMRT",
        ],
        "CAMARA_GAMMA": [
            "CENTELLOGRAMA OSEO",
            "CENTELLOGRAMA RENAL",
            "CENTELLOGRAMA DE TIROIDES",
            "ESTUDIO DINAMICO RENAL",
            "CURVA DE CAPTACION TIROIDEA",
            "BARRIDO CORPORAL TOTAL"
        ],
        "CONSULTA_MEDICA": [
            "CONSULTA",
            "CONTROL",
            "RECETA",
            "CERTIFICADO"
        ]
    }

    for categoria, practicas in categorias.items():
        for nombre in practicas:
            if not db.query(Practica).filter_by(nombre=nombre).first():
                db.add(Practica(nombre=nombre, categoria=CategoriaPractica[categoria]))

    db.commit()


def seed_agendas(db: Session):
    from models.agenda import Agenda
    
    # Agendas de Servicios
    servicios = [
        {"nombre": "QUIMIOTERAPIA SAN MARTIN", "tipo": "QUIMIOTERAPIA"},
        {"nombre": "QUIMIOTERAPIA COLOMBIA", "tipo": "QUIMIOTERAPIA"},
        {"nombre": "RADIOTERAPIA SAN MARTIN", "tipo": "RADIOTERAPIA"},
        {"nombre": "RADIOTERAPIA COLOMBIA", "tipo": "RADIOTERAPIA"},
        {"nombre": "TOMOGRAFIAS Y RX", "tipo": "TOMOGRAFIA"},
        {"nombre": "ECOGRAFIAS", "tipo": "ECOGRAFIA"},
        {"nombre": "CAMARA GAMMA", "tipo": "CAMARA_GAMMA"},
        {"nombre": "PET", "tipo": "PET"},
        {"nombre": "ELECTRO Y MAPEOS", "tipo": "ELECTRO_MAPEO"},
    ]

    for servicio in servicios:
        if not db.query(Agenda).filter_by(nombre=servicio["nombre"]).first():
            db.add(Agenda(
                nombre=servicio["nombre"],
                tipo=servicio["tipo"],
                profesional=None
            ))

    # Agendas de Médicos
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

    for medico in medicos:
        nombre_agenda = f"CONSULTORIO {medico.upper()}"
        if not db.query(Agenda).filter_by(nombre=nombre_agenda).first():
            db.add(Agenda(
                nombre=nombre_agenda,
                tipo="CONSULTA_MEDICA",
                profesional=medico
            ))

    db.commit()


def init_data():
    db = SessionLocal()

    # Siempre intentar crear el usuario admin si no existe
    seed_users(db)

    # Si ya hay datos de obras sociales, prácticas y agendas, no seedear de nuevo
    from models.agenda import Agenda
    if db.query(ObraSocial).first() and db.query(Practica).first() and db.query(Agenda).first():
        print("➡️ Base de datos ya inicializada.")
        db.close()
        return

    print("⏳ Inicializando datos de Obras Sociales, Prácticas y Agendas…")
    seed_obras_sociales(db)
    seed_practicas(db)
    seed_agendas(db)
    print("✅ Datos iniciales cargados correctamente.")

    db.close()


if __name__ == "__main__":
    init_data()
