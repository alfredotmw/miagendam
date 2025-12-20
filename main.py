from fastapi import FastAPI
from database import Base, engine
from routers import user, agendas, turnos, pacientes, exports, practicas, obras_sociales
from init_data import init_data  # 👉 AGREGADO
from migration_utils import check_and_migrate_db # 👉 MIGRACIÓN
import models  # 👉 AGREGADO para registrar tablas

# Crear tablas en la base de datos
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Agenda Médica CMCNE",
    version="1.0.0",
    description="Sistema de gestión de turnos y agendas médicas para el Centro Oncológico Corrientes",
)

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
    check_and_migrate_db(engine) # 🔄 Verificar Schema antes de iniciar
    
    # 🩹 HOTFIX: Ejecutar migración de notificaciones (Render no corre scripts manuales)
    try:
        from add_notification_columns import run_migration
        print("🔧 Ejecutando migración de columnas de notificaciones...")
        run_migration()
    except Exception as e:
        print(f"⚠️ Error ejecutando migración de notificaciones: {e}")

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
from routers import medicos
app.include_router(medicos.router)

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




