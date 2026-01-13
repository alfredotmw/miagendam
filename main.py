from fastapi import FastAPI
from database import Base, engine
from routers import user, agendas, turnos, pacientes, exports, practicas, obras_sociales
from init_data import init_data, sync_new_practicas, sync_quimio_practices  # 👉 AGREGADO

from migration_utils import check_and_migrate_db # 👉 MIGRACIÓN
import models  # 👉 AGREGADO para registrar tablas
import models.plantilla # Register P2 Model
import models.patologia # Register Patologia Model

# Crear tablas en la base de datos (Moved to startup)
# Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Agenda Médica CMCNE",
    version="1.0.0",
    description="Sistema de gestión de turnos y agendas médicas para el Centro Oncológico Corrientes",
)

@app.get("/health")
def health_check():
    return {"status": "ok", "version": "v_export_fix_2.0"}

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from fastapi.staticfiles import StaticFiles
app.mount("/static", StaticFiles(directory="static"), name="static")

# 👉 SE EJECUTA AUTOMÁTICAMENTE AL ARRANCAR FastAPI
@app.on_event("startup")
def startup_event():
    print("🚀 STARTING APP - FLUSHING LOGS")
    try:
        # Create Tables first!
        # Base.metadata.create_all(bind=engine) # 🔴 COMENTADO TEMPORALMENTE
        check_and_migrate_db(engine) # 👈 FORCE MIGRATION CHECK
    except Exception as e:
        print(f"⚠️ MIGRATION/DB ERROR: {e}")

    try:
        # init_data()
        # Run Patches
        sync_new_practicas()
        sync_quimio_practices()
        from init_data import sync_arregin_setup
        sync_arregin_setup()
        
    except Exception as e:
        print(f"⚠️ INIT DATA ERROR: {e}")


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
# from routers import statistics 
# app.include_router(statistics.router)
from routers import whatsapp
app.include_router(whatsapp.router)
from routers import medicos
app.include_router(medicos.router)
from routers import historia_clinica # 👈 NUEVO
app.include_router(historia_clinica.router)

from routers import debug_ops
app.include_router(debug_ops.router)

from routers import backup
app.include_router(backup.router)

from routers import plantilla
app.include_router(plantilla.router)

from routers import radioterapia
app.include_router(radioterapia.router)

from routers import common
app.include_router(common.router)

from fastapi.responses import RedirectResponse

@app.get("/")
def home():
    return RedirectResponse(url="/static/login.html")

from fastapi import Request
from fastapi.responses import JSONResponse

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    import traceback
    return JSONResponse(
        status_code=500,
        content={"detail": f"Global Error: {str(exc)}", "traceback": traceback.format_exc()},
    )




