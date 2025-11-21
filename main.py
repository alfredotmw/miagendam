from fastapi import FastAPI
from database import Base, engine
from routers import user, agendas, turnos, pacientes, exports, practicas, obras_sociales
from init_data import init_data  # 👉 AGREGADO

# Crear tablas en la base de datos
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Agenda Médica CMCNE",
    version="1.0.0",
    description="Sistema de gestión de turnos y agendas médicas para el Centro Oncológico Corrientes",
)

from fastapi.staticfiles import StaticFiles
app.mount("/static", StaticFiles(directory="static"), name="static")

# 👉 SE EJECUTA AUTOMÁTICAMENTE AL ARRANCAR FastAPI
@app.on_event("startup")
def startup_event():
    init_data()

# Registrar routers
app.include_router(user.router)
app.include_router(agendas.router)
app.include_router(turnos.router)
app.include_router(pacientes.router)
app.include_router(exports.router)
app.include_router(practicas.router)
app.include_router(obras_sociales.router)
from routers import analytics
app.include_router(analytics.router)
from routers import whatsapp
app.include_router(whatsapp.router)

@app.get("/")
def home():
    return {"mensaje": "Sistema Agenda Médica CMCNE funcionando correctamente 🚀"}




