from sqlalchemy import Column, Integer, String
from database import Base

class Patologia(Base):
    __tablename__ = "patologias"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, unique=True, index=True, nullable=False)
