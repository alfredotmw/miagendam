from sqlalchemy import Column, Integer, ForeignKey, UniqueConstraint
from database import Base


class AgendaPractica(Base):
    __tablename__ = "agenda_practicas"

    id = Column(Integer, primary_key=True, index=True)
    agenda_id = Column(Integer, ForeignKey("agendas.id", ondelete="CASCADE"), nullable=False)
    practica_id = Column(Integer, ForeignKey("practicas.id", ondelete="CASCADE"), nullable=False)

    __table_args__ = (
        UniqueConstraint("agenda_id", "practica_id", name="uq_agenda_practica"),
    )
