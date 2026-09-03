from fastapi import APIRouter, Depends
from typing import List
from auth.jwt import get_current_user
from sqlalchemy.orm import Session
from database import get_db

router = APIRouter(
    prefix="/common",
    tags=["Common"]
)

@router.get("/patologias", response_model=List[str])
def get_common_patologias(current_user: dict = Depends(get_current_user)):
    """
    Returns a comprehensive list of oncology diagnoses for autocomplete.
    """
    return [
        "Carcinoma Ductal In Situ (Mama)",
        "Carcinoma Lobulillar In Situ (Mama)",
        "Carcinoma Ductal Invasivo (Mama)",
        "Carcinoma Lobulillar Invasivo (Mama)",
        "Cáncer de Mama Inflamatorio",
        "Enfermedad de Paget (Mama)",
        "Carcinoma de Células No Pequeñas (Pulmón)",
        "Adenocarcinoma (Pulmón)",
        "Carcinoma de Células Escamosas (Pulmón)",
        "Carcinoma de Células Grandes (Pulmón)",
        "Carcinoma de Células Pequeñas (Pulmón)",
        "Adenocarcinoma de Próstata",
        "Carcinoma de Células Renales",
        "Carcinoma Urotelial (Vejiga)",
        "Adenocarcinoma de Colon",
        "Adenocarcinoma de Recto",
        "Carcinoma de Células Escamosas (Ano)",
        "Carcinoma de Células Escamosas (Cabeza y Cuello)",
        "Carcinoma Nasofaríngeo",
        "Glioblastoma Multiforme",
        "Astrocitoma",
        "Meningioma",
        "Meduloblastoma",
        "Melanoma",
        "Carcinoma Basocelular (Piel)",
        "Carcinoma Espinocelular (Piel)",
        "Adenocarcinoma Gástrico",
        "GIST (Tumor del Estroma Gastrointestinal)",
        "Adenocarcinoma de Páncreas",
        "Carcinoma Hepatocelular (Hígado)",
        "Colangiocarcinoma",
        "Carcinoma de Ovario Epitelial",
        "Tumor de Células Germinales",
        "Adenocarcinoma de Endometrio",
        "Sarcoma Uterino",
        "Carcinoma de Cuello Uterino (Cervix)",
        "Linfoma de Hodgkin",
        "Linfoma No Hodgkin",
        "Leucemia Mieloide Aguda",
        "Leucemia Linfoide Crónica",
        "Mieloma Múltiple",
        "Sarcoma de Ewing",
        "Osteosarcoma",
        "Condrosarcoma",
        "Rabdomiosarcoma",
        "Leiomiosarcoma",
        "Liposarcoma",
        "Metástasis Ósea",
        "Metástasis Cerebral",
        "Metástasis Hepática",
        "Metástasis Pulmonar",
        "Metástasis Ganglionar",
        "Tumor Neuroendocrino",
        "Timoma",
        "Mesotelioma",
        "Otro"
    ]

from models.medico import MedicoDerivante
from typing import Dict

@router.get("/medicos-derivantes", response_model=List[Dict[str, object]]) # Returns list of dicts {id, nombre}
def get_medicos_derivantes(db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    """
    Returns a list of all registered referring physicians.
    """
    medicos = db.query(MedicoDerivante).order_by(MedicoDerivante.nombre.asc()).all()
    return [{"id": m.id, "nombre": m.nombre} for m in medicos]

@router.get("/settings")
def get_settings(current_user: dict = Depends(get_current_user)):
    """
    Returns public settings configuration required by the frontend.
    """
    import config
    return {
        "enable_clinical_reports": getattr(config, "ENABLE_CLINICAL_REPORTS", False)
    }
