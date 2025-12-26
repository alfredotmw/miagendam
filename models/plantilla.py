from sqlalchemy import Column, Integer, String, Text, ForeignKey
from sqlalchemy.orm import relationship
from database import Base

class Plantilla(Base):
    __tablename__ = "plantillas"

    id = Column(Integer, primary_key=True, index=True)
    titulo = Column(String, nullable=False)
    contenido = Column(Text, nullable=False) # The template text
    servicio = Column(String, nullable=True) # Optional filter, e.g. "ONCOLOGIA"
    
    creado_por_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    creado_por = relationship("User", backref="plantillas")
