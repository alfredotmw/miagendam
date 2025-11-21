from database import Base, engine
from models.user import User
from models.agenda import Agenda
from models.turno import Turno
from models.paciente import Paciente

print("🧱 Creando tablas en la base de datos...")

# Crea todas las tablas definidas en los modelos
Base.metadata.create_all(bind=engine)

print("✅ Tablas creadas correctamente:")
print(" - usuarios")
print(" - agendas")
print(" - pacientes")
print(" - turnos")
