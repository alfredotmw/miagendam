# routers/feriados.py
"""Feriados y plan de sesiones de radioterapia (lunes a viernes, sin feriados).

Módulo aislado: tabla propia (feriados) y endpoints nuevos. No cambia el alta de
turnos: el plan solo CALCULA fechas y disponibilidad; los turnos se siguen creando
uno por uno con POST /turnos/ y todas sus validaciones de siempre.
Nunca se borran feriados: se desactivan.
"""
import json
import urllib.request
from datetime import date, datetime, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from auth.jwt import get_current_user
from database import get_db
from models.feriado import Feriado

router = APIRouter(tags=["Feriados y plan de radioterapia"])

NO_DISPONIBLE = "Los feriados no están disponibles en este momento."
FUENTE_NACIONAL = "https://api.argentinadatos.com/v1/feriados/{anio}"
MAX_SESIONES = 60

# Calendario oficial 2026 (argentina.gob.ar / argentina.travel): feriados y días
# no laborables con fines turísticos. Se carga solo si la tabla está vacía.
SEMILLA_2026 = [
    ("2026-01-01", "Año Nuevo", "inamovible"),
    ("2026-02-16", "Carnaval", "inamovible"),
    ("2026-02-17", "Carnaval", "inamovible"),
    ("2026-03-23", "Día no laborable con fines turísticos", "puente"),
    ("2026-03-24", "Día Nacional de la Memoria por la Verdad y la Justicia", "inamovible"),
    ("2026-04-02", "Día del Veterano y de los Caídos en la Guerra de Malvinas", "inamovible"),
    ("2026-04-03", "Viernes Santo", "inamovible"),
    ("2026-05-01", "Día del Trabajador", "inamovible"),
    ("2026-05-25", "Día de la Revolución de Mayo", "inamovible"),
    ("2026-06-15", "Paso a la Inmortalidad del Gral. Martín Miguel de Güemes", "trasladable"),
    ("2026-06-20", "Paso a la Inmortalidad del Gral. Manuel Belgrano", "inamovible"),
    ("2026-07-09", "Día de la Independencia", "inamovible"),
    ("2026-07-10", "Día no laborable con fines turísticos", "puente"),
    ("2026-08-17", "Paso a la Inmortalidad del Gral. José de San Martín", "trasladable"),
    ("2026-10-12", "Día del Respeto a la Diversidad Cultural", "trasladable"),
    ("2026-11-23", "Día de la Soberanía Nacional", "trasladable"),
    ("2026-12-07", "Día no laborable con fines turísticos", "puente"),
    ("2026-12-08", "Inmaculada Concepción de María", "inamovible"),
    ("2026-12-25", "Navidad", "inamovible"),
]


def _rol(user: dict) -> str:
    return str(user.get("role") or "").upper()


def _solo_admin(user: dict) -> None:
    if _rol(user) != "ADMIN":
        raise HTTPException(403, "Solo administración puede modificar feriados.")


def _sembrar(db: Session) -> None:
    if db.query(Feriado.id).first() is not None:
        return
    for f, nombre, tipo in SEMILLA_2026:
        db.add(Feriado(fecha=date.fromisoformat(f), nombre=nombre, tipo=tipo, origen="nacional"))
    db.commit()


def _tabla(db: Session):
    try:
        _sembrar(db)
        return db.query(Feriado)
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(503, NO_DISPONIBLE)


def feriados_activos(db: Session, desde: date, hasta: date) -> dict:
    """{fecha: nombre} de feriados activos en el rango (incluye ambos extremos)."""
    q = _tabla(db).filter(Feriado.activo.is_(True), Feriado.fecha >= desde, Feriado.fecha <= hasta)
    return {f.fecha: f.nombre for f in q.all()}


def anios_cargados(db: Session) -> set:
    return {f.fecha.year for f in _tabla(db).filter(Feriado.origen == "nacional").all()}


def dias_de_tratamiento(inicio: date, sesiones: int, feriados: dict) -> List[date]:
    """`sesiones` días hábiles desde `inicio` (incluido): lunes a viernes, sin feriados."""
    dias, d = [], inicio
    while len(dias) < sesiones:
        if d.weekday() < 5 and d not in feriados:
            dias.append(d)
        d += timedelta(days=1)
    return dias


def _salida(f: Feriado) -> dict:
    return {"id": f.id, "fecha": f.fecha.isoformat(), "nombre": f.nombre, "tipo": f.tipo,
            "origen": f.origen, "activo": bool(f.activo)}


class FeriadoIn(BaseModel):
    fecha: date
    nombre: str = Field(min_length=2, max_length=200)
    tipo: str = Field(default="sin_servicio", max_length=40)


class ActivoIn(BaseModel):
    activo: bool


@router.get("/feriados")
def listar_feriados(anio: Optional[int] = Query(default=None, ge=2020, le=2100),
                    db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    q = _tabla(db)
    if anio:
        q = q.filter(Feriado.fecha >= date(anio, 1, 1), Feriado.fecha <= date(anio, 12, 31))
    return [_salida(f) for f in q.order_by(Feriado.fecha).all()]


@router.post("/feriados")
def agregar_feriado(data: FeriadoIn, db: Session = Depends(get_db),
                    current_user: dict = Depends(get_current_user)):
    _solo_admin(current_user)
    existente = _tabla(db).filter(Feriado.fecha == data.fecha).first()
    if existente:
        existente.nombre, existente.tipo, existente.activo = data.nombre.strip(), data.tipo, True
        existente.modificado_por_id, existente.fecha_modificacion = current_user.get("id"), datetime.now()
        db.commit()
        return _salida(existente)
    f = Feriado(fecha=data.fecha, nombre=data.nombre.strip(), tipo=data.tipo, origen="manual",
                creado_por_id=current_user.get("id"))
    db.add(f)
    db.commit()
    db.refresh(f)
    return _salida(f)


@router.put("/feriados/{feriado_id}/activo")
def activar_feriado(feriado_id: int, data: ActivoIn, db: Session = Depends(get_db),
                    current_user: dict = Depends(get_current_user)):
    """No se borra: se desactiva (por ejemplo, si el centro decide atender ese día)."""
    _solo_admin(current_user)
    f = _tabla(db).filter(Feriado.id == feriado_id).first()
    if not f:
        raise HTTPException(404, "Feriado no encontrado")
    f.activo = data.activo
    f.modificado_por_id, f.fecha_modificacion = current_user.get("id"), datetime.now()
    db.commit()
    return _salida(f)


def _bajar_nacionales(anio: int) -> list:
    req = urllib.request.Request(FUENTE_NACIONAL.format(anio=anio), headers={"Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=15) as r:
        data = json.loads(r.read().decode("utf-8"))
    if not isinstance(data, list):
        raise ValueError("respuesta inesperada")
    return data


@router.post("/feriados/actualizar-nacionales")
def actualizar_nacionales(anio: int = Query(..., ge=2024, le=2100), db: Session = Depends(get_db),
                          current_user: dict = Depends(get_current_user)):
    """Agrega los feriados nacionales del año desde el calendario oficial publicado.
    Solo agrega los que faltan; no modifica ni quita lo que ya está cargado."""
    _solo_admin(current_user)
    try:
        filas = _bajar_nacionales(anio)
    except Exception:
        raise HTTPException(502, "No se pudo consultar el calendario de feriados nacionales. Probá más tarde "
                                 "o cargalos a mano.")
    existentes = {f.fecha for f in _tabla(db).all()}
    nuevos = 0
    for fila in filas:
        try:
            fecha = date.fromisoformat(str(fila.get("fecha"))[:10])
        except ValueError:
            continue
        if fecha.year != anio or fecha in existentes:
            continue
        db.add(Feriado(fecha=fecha, nombre=str(fila.get("nombre") or "Feriado")[:200],
                       tipo=str(fila.get("tipo") or "feriado")[:40], origen="nacional",
                       creado_por_id=current_user.get("id")))
        existentes.add(fecha)
        nuevos += 1
    db.commit()
    return {"anio": anio, "agregados": nuevos}


class PlanIn(BaseModel):
    agenda_id: int
    fecha_inicio: date
    sesiones: int = Field(ge=1, le=MAX_SESIONES)
    hora: str = Field(pattern=r"^\d{2}:\d{2}")
    practicas_ids: List[int] = Field(min_length=1)
    paciente_id: Optional[int] = None
    duracion: int = Field(default=10, ge=5, le=240)


@router.post("/turnos/plan-radioterapia")
def plan_radioterapia(plan: PlanIn, db: Session = Depends(get_db),
                      current_user: dict = Depends(get_current_user)):
    """Calcula las fechas del tratamiento (lunes a viernes, sin feriados) y si hay
    lugar a esa hora cada día. No crea turnos."""
    from models.agenda import Agenda
    from models.practica import Practica
    from services.turno_service import check_availability_boolean

    agenda = db.get(Agenda, plan.agenda_id)
    if not agenda:
        raise HTTPException(404, "Agenda no encontrada")
    practicas = db.query(Practica).filter(Practica.id.in_(plan.practicas_ids)).all()
    h, m = map(int, plan.hora.split(":")[:2])
    tope = plan.fecha_inicio + timedelta(days=plan.sesiones * 3 + 60)
    feriados = feriados_activos(db, plan.fecha_inicio, tope)
    dias = dias_de_tratamiento(plan.fecha_inicio, plan.sesiones, feriados)
    salteados = [{"fecha": f.isoformat(), "nombre": n} for f, n in sorted(feriados.items())
                 if plan.fecha_inicio <= f <= dias[-1] and f.weekday() < 5]
    sesiones = []
    for i, d in enumerate(dias, 1):
        libre = check_availability_boolean(db, agenda.id, datetime(d.year, d.month, d.day, h, m), plan.duracion,
                                           agenda.tipo, paciente_id=plan.paciente_id, practicas=practicas)
        sesiones.append({"numero": i, "fecha": d.isoformat(), "hora": plan.hora[:5], "disponible": bool(libre)})
    cargados = anios_cargados(db)
    sin_feriados = sorted({d.year for d in dias} - cargados)
    return {"sesiones": sesiones, "desde": dias[0].isoformat(), "hasta": dias[-1].isoformat(),
            "feriados_salteados": salteados, "ocupados": sum(1 for s in sesiones if not s["disponible"]),
            "anios_sin_feriados": sin_feriados}
