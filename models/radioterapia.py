from sqlalchemy import Column, Integer, String, Date, Text, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime

class SeguimientoRadioterapia(Base):
    __tablename__ = "seguimiento_radioterapia"

    id = Column(Integer, primary_key=True, index=True)
    paciente_id = Column(Integer, ForeignKey("pacientes.id"), nullable=False)
    
    patologia = Column(String, nullable=True) # e.g. "Ca. Mama", "Ca. Próstata"
    medico_derivante = Column(String, nullable=True) # Doctor that sent the patient
    sede = Column(String, nullable=True) # "San Martín" or "Colombia"
    tipo_tecnica = Column(String, nullable=True) # "IMRT" or "RT 3D"
    
    # Dates
    fecha_consulta = Column(Date, nullable=True)
    fecha_tac = Column(Date, nullable=True) # Simulation CT
    fecha_inicio = Column(Date, nullable=True) # Start of Treatment
    fecha_fin = Column(Date, nullable=True) # End of Treatment
    
    medico_responsable = Column(String, nullable=True) # e.g. "Dra. Duarte" (Textual or could be linked to User if we enforce it)
    observaciones = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # Auditoría extendida
    creado_por_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    modificado_por_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    creado_por = relationship("User", foreign_keys=[creado_por_id])
    modificado_por = relationship("User", foreign_keys=[modificado_por_id])

    # Relationship
    paciente = relationship("Paciente", backref="tratamientos_radioterapia")
