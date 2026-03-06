from sqlalchemy import Column, Integer, ForeignKey, Table
from database import Base

# Association table for Many-to-Many relationship between User and Agenda
user_agendas = Table(
    "user_agendas",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("agenda_id", Integer, ForeignKey("agendas.id", ondelete="CASCADE"), primary_key=True),
)
