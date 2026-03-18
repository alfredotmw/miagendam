from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Date, Boolean, JSON
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime

class HistoriaClinica(Base):
    __tablename__ = "historia_clinica"

    id = Column(Integer, primary_key=True, index=True)
    paciente_id = Column(Integer, ForeignKey("pacientes.id"), nullable=False)
    medico_id = Column(Integer, ForeignKey("users.id"), nullable=True) # Opcional: si queremos saber quien escribio
    especialidad_medico = Column(String, nullable=True) # Especialidad del médico al crear la nota
    tipo_evolucion = Column(String, nullable=True) # "oncologia" o "general" - Definido por la interfaz
    
    fecha = Column(DateTime, default=datetime.now)
    texto = Column(Text, nullable=True) # Mantener como fallback o resumen
    servicio = Column(String, nullable=False) # CONSULTORIO, QUIMIOTERAPIA, ETC.
    requiere_radioterapia = Column(Boolean, default=False) # 👈 NUEVO: Indicar si requiere radioterapia

    # Campos Estructurados (Ley 26.529 / Requerimiento User)
    motivo_consulta = Column(Text, nullable=True)
    antecedentes = Column(Text, nullable=True) # Personales, Familiares, Enfermedad Actual
    examen_clinico = Column(Text, nullable=True) # Incluye Diagnostico Probable
    plan_estudio = Column(Text, nullable=True)
    diagnostico_diferencial = Column(Text, nullable=True)
    tratamiento = Column(Text, nullable=True)
    evolucion = Column(Text, nullable=True) # Pronostico y Evolucion
    patologia = Column(Text, nullable=True) # 👈 NUEVO: Diagnostico Principal / Patologia Especifica

    # P0: Estados y Auditoría
    estado = Column(String, default="BORRADOR") # BORRADOR, FIRMADO, ANULADO
    
    creado_por_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    fecha_creacion = Column(DateTime, default=datetime.now)
    
    editado_por_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    fecha_edicion = Column(DateTime, nullable=True, onupdate=datetime.now)
    
    firmado_por_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    fecha_firma = Column(DateTime, nullable=True)
    
    es_enmienda_de_id = Column(Integer, ForeignKey("historia_clinica.id"), nullable=True)

    # P1: Oncology Fields
    ecog = Column(Integer, nullable=True) # 0-5
    tnm = Column(String, nullable=True)
    estadio = Column(String, nullable=True)
    toxicidad = Column(Text, nullable=True)

    # P2: Structured Evolution Redesign
    examen_fisico_estructurado = Column(JSON, nullable=True)
    indicaciones = Column(JSON, nullable=True)
    proximo_control = Column(Date, nullable=True)
    pautas_alarma = Column(Text, nullable=True)
    situacion_cierre = Column(String, nullable=True)

    # Relaciones
    paciente = relationship("Paciente", back_populates="historia_clinica")
    medico = relationship("User", foreign_keys=[medico_id], backref="historias_creadas") # Medico principal (compatibilidad)
    
    creado_por = relationship("User", foreign_keys=[creado_por_id])
    editado_por = relationship("User", foreign_keys=[editado_por_id])
    firmado_por = relationship("User", foreign_keys=[firmado_por_id])
    enmienda_de = relationship("HistoriaClinica", remote_side=[id], backref="enmiendas")
