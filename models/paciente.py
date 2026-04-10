from sqlalchemy import Column, Integer, String, Date, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime
from models.user import User # Necesario para relación audit

class Paciente(Base):
    __tablename__ = "pacientes"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, nullable=False)
    apellido = Column(String, nullable=False)
    dni = Column(String, unique=True, nullable=False)
    fecha_nacimiento = Column(Date, nullable=True)
    sexo = Column(String, nullable=True) # F, M, X, etc.
    telefono = Column(String, nullable=True) # Mantenemos telefono como genérico
    celular = Column(String, nullable=True)  # Campo específico para celular (WhatsApp)
    email = Column(String, nullable=True)
    direccion = Column(String, nullable=True)
    nro_afiliado = Column(String, nullable=True) # Nuevo campo
    # patologia = Column(String, nullable=True) # Nuevo campo centralizado
    obra_social_id = Column(Integer, ForeignKey("obras_sociales.id"), nullable=True)

    # Relaciones
    obra_social = relationship("ObraSocial", back_populates="pacientes")

    # Auditoría
    creado_por_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    fecha_creacion = Column(DateTime, default=datetime.now)
    modificado_por_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    fecha_modificacion = Column(DateTime, nullable=True, onupdate=datetime.now)

    creado_por = relationship("User", foreign_keys=[creado_por_id])
    modificado_por = relationship("User", foreign_keys=[modificado_por_id])
    
    # Nueva relación para Historia Clínica
    historia_clinica = relationship("HistoriaClinica", back_populates="paciente", cascade="all, delete-orphan")
    turnos = relationship("Turno", back_populates="paciente")
    
    # Nuevo campo para médico derivante preferido
    medico_derivante_id = Column(Integer, ForeignKey("medicos_derivantes.id"), nullable=True)
    medico_derivante = relationship("MedicoDerivante") # Unidireccional o back_populates si se quiere

    @property
    def edad(self):
        if not self.fecha_nacimiento:
            return None
        from datetime import date
        today = date.today()
        return today.year - self.fecha_nacimiento.year - ((today.month, today.day) < (self.fecha_nacimiento.month, self.fecha_nacimiento.day))
