from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from database import get_db
from models.paciente import Paciente
from models.obra_social import ObraSocial
from schemas.paciente import PacienteCreate, PacienteUpdate, PacienteOut
from typing import List, Optional
from datetime import date

router = APIRouter(
    prefix="/pacientes",
    tags=["Pacientes"]
)

# 🟢 Crear paciente
from auth.jwt import get_current_user

@router.post("/", response_model=PacienteOut)
def crear_paciente(paciente: PacienteCreate, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    existente = db.query(Paciente).filter(Paciente.dni == paciente.dni).first()
    if existente:
        raise HTTPException(status_code=400, detail="Ya existe un paciente con ese DNI")
    
    # Manejo de Obra Social dinámica (OBLIGATORIO)
    if not paciente.obra_social_id and not paciente.obra_social_nombre:
        raise HTTPException(status_code=400, detail="La Obra Social es obligatoria")

    if paciente.obra_social_nombre:
        nombre_os = paciente.obra_social_nombre.strip().upper() # FORCE UPPERCASE
        os_existente = db.query(ObraSocial).filter(ObraSocial.nombre == nombre_os).first()
        if os_existente:
            paciente.obra_social_id = os_existente.id
        else:
            nueva_os = ObraSocial(nombre=nombre_os)
            db.add(nueva_os)
            db.commit()
            db.refresh(nueva_os)
            paciente.obra_social_id = nueva_os.id

    # Excluir obra_social_nombre del dict antes de crear el modelo
    paciente_data = paciente.dict(exclude={"obra_social_nombre"})
    
    # FORCE UPPERCASE for text fields
    if paciente_data.get('nombre'): paciente_data['nombre'] = paciente_data['nombre'].upper()
    if paciente_data.get('apellido'): paciente_data['apellido'] = paciente_data['apellido'].upper()
    if paciente_data.get('sexo'): paciente_data['sexo'] = paciente_data['sexo'].upper()
    if paciente_data.get('direccion'): paciente_data['direccion'] = paciente_data['direccion'].upper()

    nuevo = Paciente(**paciente_data)
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
    return nuevo


# 🟢 Listar pacientes con filtro
@router.get("/", response_model=List[PacienteOut])
def listar_pacientes(
    q: Optional[str] = Query(None, description="Buscar por DNI, nombre o apellido"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    query = db.query(Paciente)
    if q:
        query = query.filter(
            (Paciente.dni.contains(q)) |
            (Paciente.nombre.ilike(f"%{q}%")) |
            (Paciente.apellido.ilike(f"%{q}%"))
        )
    pacientes = query.offset(offset).limit(limit).all()
    return pacientes


# 🟢 Obtener un paciente por ID
@router.get("/{paciente_id}", response_model=PacienteOut)
def obtener_paciente(paciente_id: int, db: Session = Depends(get_db)):
    paciente = db.query(Paciente).filter(Paciente.id == paciente_id).first()
    if not paciente:
        raise HTTPException(status_code=404, detail="Paciente no encontrado")
    return paciente


# 🟢 Obtener un paciente por DNI
@router.get("/dni/{dni}", response_model=PacienteOut)
def obtener_paciente_por_dni(dni: str, db: Session = Depends(get_db)):
    paciente = db.query(Paciente).filter(Paciente.dni == dni).first()
    if not paciente:
        raise HTTPException(status_code=404, detail="Paciente no encontrado")
    return paciente


# 🟢 Actualizar paciente
@router.put("/{paciente_id}", response_model=PacienteOut)
def actualizar_paciente(paciente_id: int, datos: PacienteUpdate, db: Session = Depends(get_db)):
    paciente = db.query(Paciente).filter(Paciente.id == paciente_id).first()
    if not paciente:
        raise HTTPException(status_code=404, detail="Paciente no encontrado")

    # Manejo de Obra Social dinámica en update
    if datos.obra_social_nombre:
        nombre_os = datos.obra_social_nombre.strip().upper() # FORCE UPPERCASE
        os_existente = db.query(ObraSocial).filter(ObraSocial.nombre == nombre_os).first()
        if os_existente:
            datos.obra_social_id = os_existente.id
        else:
            nueva_os = ObraSocial(nombre=nombre_os)
            db.add(nueva_os)
            db.commit()
            db.refresh(nueva_os)
            datos.obra_social_id = nueva_os.id
    
    # Excluir obra_social_nombre del dict antes de actualizar
    update_data = datos.dict(exclude_unset=True, exclude={"obra_social_nombre"})
    
    for key, value in update_data.items():
        if isinstance(value, str): # FORCE UPPERCASE
            value = value.upper()
        setattr(paciente, key, value)
    
    db.commit()
    db.refresh(paciente)
    return paciente


# 🟢 Eliminar paciente
@router.delete("/{paciente_id}")
def eliminar_paciente(paciente_id: int, db: Session = Depends(get_db)):
    paciente = db.query(Paciente).filter(Paciente.id == paciente_id).first()
    if not paciente:
        raise HTTPException(status_code=404, detail="Paciente no encontrado")
    db.delete(paciente)
    db.commit()
    return {"mensaje": f"Paciente '{paciente.nombre} {paciente.apellido}' eliminado correctamente"}


# 🟢 Vista combinada: Detalle de pacientes
@router.get("/detalle/", summary="Lista pacientes con obra social y edad calculada")
def detalle_pacientes(db: Session = Depends(get_db)):
    pacientes = (
        db.query(
            Paciente.id,
            Paciente.nombre,
            Paciente.apellido,
            Paciente.dni,
            Paciente.fecha_nacimiento,
            Paciente.telefono,
            Paciente.email,
            Paciente.direccion,
            ObraSocial.nombre.label("obra_social"),
        )
        .outerjoin(ObraSocial, Paciente.obra_social_id == ObraSocial.id)
        .order_by(Paciente.apellido)
        .all()
    )

    def calcular_edad(fecha_nacimiento):
        if not fecha_nacimiento:
            return None
        hoy = date.today()
        return hoy.year - fecha_nacimiento.year - (
            (hoy.month, hoy.day) < (fecha_nacimiento.month, fecha_nacimiento.day)
        )

    resultado = []
    for p in pacientes:
        resultado.append({
            "id": p.id,
            "nombre": p.nombre,
            "apellido": p.apellido,
            "dni": p.dni,
            "fecha_nacimiento": p.fecha_nacimiento,
            "edad": calcular_edad(p.fecha_nacimiento),
            "telefono": p.telefono,
            "email": p.email,
            "direccion": p.direccion,
            "obra_social": p.obra_social
        })

    return resultado



