from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from database import get_db
from models.paciente import Paciente
from models.obra_social import ObraSocial
from models.medico import MedicoDerivante # 👈 Import
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
    # 🟢 Normalize DNI: Remove dots, spaces, dashes
    if paciente.dni:
        paciente.dni = paciente.dni.replace('.', '').replace(' ', '').replace('-', '').strip()

    existente = db.query(Paciente).filter(Paciente.dni == paciente.dni).first()
    if existente:
        raise HTTPException(status_code=400, detail=f"Ya existe un paciente con ese DNI ({paciente.dni})")
    
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

    # Manejo de Medico Derivante (Opcional)
    if paciente.medico_derivante_nombre:
        nombre_med = paciente.medico_derivante_nombre.strip().upper()
        if nombre_med:
            med_existente = db.query(MedicoDerivante).filter(MedicoDerivante.nombre == nombre_med).first()
            if med_existente:
                paciente.medico_derivante_id = med_existente.id
            else:
                nuevo_med = MedicoDerivante(nombre=nombre_med)
                db.add(nuevo_med)
                db.commit()
                db.refresh(nuevo_med)
                paciente.medico_derivante_id = nuevo_med.id

    # Excluir campos extra del dict antes de crear el modelo
    paciente_data = paciente.dict(exclude={"obra_social_nombre", "medico_derivante_nombre"})
    
    # FORCE UPPERCASE for text fields
    if paciente_data.get('nombre'): paciente_data['nombre'] = paciente_data['nombre'].upper()
    if paciente_data.get('apellido'): paciente_data['apellido'] = paciente_data['apellido'].upper()
    if paciente_data.get('sexo'): paciente_data['sexo'] = paciente_data['sexo'].upper()
    if paciente_data.get('direccion'): paciente_data['direccion'] = paciente_data['direccion'].upper()
    if paciente_data.get('patologia'): paciente_data['patologia'] = paciente_data['patologia'].strip().upper()

    nuevo = Paciente(**paciente_data)
    nuevo.creado_por_id = current_user.get("id") # 🛡️ Auditoría
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
    dni_norm = dni.replace('.', '').replace(' ', '').replace('-', '').strip()
    paciente = db.query(Paciente).filter(Paciente.dni == dni_norm).first()
    if not paciente:
        raise HTTPException(status_code=404, detail="Paciente no encontrado")
    return paciente


# 🟢 Actualizar paciente
@router.put("/{paciente_id}", response_model=PacienteOut)
def actualizar_paciente(paciente_id: int, datos: PacienteUpdate, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    paciente = db.query(Paciente).filter(Paciente.id == paciente_id).first()
    if not paciente:
        raise HTTPException(status_code=404, detail="Paciente no encontrado")

    # 🟢 Normalize DNI if being updated
    if datos.dni:
        datos.dni = datos.dni.replace('.', '').replace(' ', '').replace('-', '').strip()
        # Optional: Check if new DNI collides with another patient?
        # The unique constraint in DB might catch it, but manual check is cleaner
        if datos.dni != paciente.dni:
            existente = db.query(Paciente).filter(Paciente.dni == datos.dni).first()
            if existente:
                raise HTTPException(status_code=400, detail=f"El DNI {datos.dni} ya lo tiene otro paciente.")

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
    
    # Manejo de Medico Derivante en update
    if datos.medico_derivante_nombre:
        nombre_med = datos.medico_derivante_nombre.strip().upper()
        if nombre_med:
            med_existente = db.query(MedicoDerivante).filter(MedicoDerivante.nombre == nombre_med).first()
            if med_existente:
                datos.medico_derivante_id = med_existente.id
            else:
                nuevo_med = MedicoDerivante(nombre=nombre_med)
                db.add(nuevo_med)
                db.commit()
                db.refresh(nuevo_med)
                datos.medico_derivante_id = nuevo_med.id

    # Excluir campos extra del dict antes de actualizar
    # IMPORTANT: We explicitly exclude the *names* so they don't try to write to the DB columns that don't exist
    # But we MUST ensure the *IDs* (which might have been set above) are INCLUDED in the update.
    # The problem with 'exclude_unset=True' is that if the ID wasn't in the JSON payload (it wasn't), it's considered unset.
    # So we must manually merge our resolved IDs into the update data.
    
    update_data = datos.dict(exclude_unset=True, exclude={"obra_social_nombre", "medico_derivante_nombre"})
    
    # Manually inject the resolved IDs if they were determined above
    if datos.obra_social_id:
        update_data['obra_social_id'] = datos.obra_social_id
    
    if datos.medico_derivante_id:
        update_data['medico_derivante_id'] = datos.medico_derivante_id

    for key, value in update_data.items():
        if isinstance(value, str): # FORCE UPPERCASE & STRIP
            value = value.strip().upper()
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



