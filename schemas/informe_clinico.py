# schemas/informe_clinico.py

from pydantic import BaseModel, Field, Extra, validator
from datetime import datetime
from typing import Optional, Dict, Union

# Define strict sub-models for each report template
class ImagenesTemplate(BaseModel):
    indicacion_clinica: str = Field(..., max_length=2000)
    tecnica: str = Field(..., max_length=4000)
    hallazgos: str = Field(..., max_length=10000)
    conclusion: str = Field(..., max_length=4000)
    observaciones: str = Field(..., max_length=4000)

    class Config:
        extra = Extra.forbid

class ElectroencefalogramaTemplate(BaseModel):
    indicacion_clinica: str = Field(..., max_length=2000)
    tecnica: str = Field(..., max_length=4000)
    actividad_de_fondo: str = Field(..., max_length=6000)
    hallazgos: str = Field(..., max_length=10000)
    maniobras_de_activacion: str = Field(..., max_length=6000)
    conclusion: str = Field(..., max_length=4000)
    observaciones: str = Field(..., max_length=4000)

    class Config:
        extra = Extra.forbid

class ConsultaMedicaTemplate(BaseModel):
    motivo_consulta: str = Field(..., max_length=3000)
    antecedentes_relevantes: str = Field(..., max_length=6000)
    evaluacion: str = Field(..., max_length=10000)
    impresion_diagnostica: str = Field(..., max_length=5000)
    conducta: str = Field(..., max_length=5000)
    indicaciones: str = Field(..., max_length=5000)
    observaciones: str = Field(..., max_length=4000)

    class Config:
        extra = Extra.forbid

class TextoLibreTemplate(BaseModel):
    informe: str = Field(..., max_length=15000)

    class Config:
        extra = Extra.forbid

# Payload validation helper
def validate_content_json(tipo_informe: str, contenido_json: Dict) -> Dict:
    # Closed list of report types
    valid_types = {
        "IMAGENES": ImagenesTemplate,
        "ELECTROENCEFALOGRAMA": ElectroencefalogramaTemplate,
        "CONSULTA_MEDICA": ConsultaMedicaTemplate,
        "TEXTO_LIBRE": TextoLibreTemplate
    }
    
    if tipo_informe not in valid_types:
        raise ValueError(f"Tipo de informe inválido: {tipo_informe}. Permitidos: {list(valid_types.keys())}")
    
    # Validate using corresponding pydantic model
    template_model = valid_types[tipo_informe]
    # This will validate data types, max lengths, and forbid extra keys
    validated_obj = template_model(**contenido_json)
    
    # Extra check: forbid base64/binary signatures/attachments
    for k, v in validated_obj.dict().items():
        if isinstance(v, str):
            if "data:image" in v or "base64" in v:
                raise ValueError(f"El campo '{k}' contiene contenido binario o base64 no permitido.")
                
    return validated_obj.dict()


# Main schemas
class InformeClinicoCreate(BaseModel):
    tipo_informe: str = Field(..., max_length=50)
    contenido_json: Dict

    class Config:
        extra = Extra.forbid

    @validator("tipo_informe")
    def validate_type(cls, v):
        allowed = ["IMAGENES", "ELECTROENCEFALOGRAMA", "CONSULTA_MEDICA", "TEXTO_LIBRE"]
        if v not in allowed:
            raise ValueError(f"Tipo de informe no permitido. Valores válidos: {allowed}")
        return v

class InformeClinicoUpdate(BaseModel):
    contenido_json: Dict
    version: int

    class Config:
        extra = Extra.forbid

class InformeClinicoFinalize(BaseModel):
    version: int

    class Config:
        extra = Extra.forbid

# Output schemas depending on user role
class InformeClinicoOut(BaseModel):
    id: int
    turno_id: int
    paciente_id: int
    tipo_informe: str
    contenido_json: Dict
    contenido_texto: Optional[str]
    estado: str
    version: int
    created_at: datetime
    updated_at: datetime
    finalized_at: Optional[datetime]
    created_by: int
    updated_by: int
    finalized_by: Optional[int]
    finalized_by_username: Optional[str] = None  # Enriched by router for display

    class Config:
        orm_mode = True
        from_attributes = True

    @validator("created_at", "updated_at", "finalized_at", pre=True, allow_reuse=True)
    def ensure_utc(cls, v):
        if v is None:
            return None
        if isinstance(v, datetime):
            if v.tzinfo is None:
                from datetime import timezone
                return v.replace(tzinfo=timezone.utc)
        return v

class InformeClinicoReceptionOut(BaseModel):
    turno_id: int
    estado: str

    class Config:
        orm_mode = True
        from_attributes = True
