# routers/estudios_sin_informe.py
"""Consulta de estudios realizados que todavía no tienen informe.

SOLO LECTURA: este módulo hace únicamente SELECT. No crea tablas, no agrega columnas
ni modifica/borra registros. Si algo falla (p. ej. falta una tabla), responde 503 y
el resto del sistema sigue igual.

Reglas (definidas por administración, 25/11/2026):
  - Solo turnos en estado COMPLETADO.
  - Servicios que llevan informe: TOMOGRAFIA (TAC y RX), ECOGRAFIA, ELECTRO_MAPEO,
    PET, CAMARA_GAMMA y QUIMIOTERAPIA (cada sesión). RADIOTERAPIA no lleva informe
    por sesión y no se lista. Configurable con la variable ESTUDIO_AGENDA_TIPOS.
  - Varios estudios del mismo paciente, mismo servicio, mismo día y mismo horario
    llevan UN solo informe: se muestran en una fila y, si cualquiera de esos turnos
    ya tiene informe, el grupo entero cuenta como informado.
  - Cuenta como informe: link de Visual Médica, PDF, informe clínico FINALIZADO o
    RECTIFICADO y, en quimioterapia, además una evolución FIRMADA del paciente en
    historia clínica ese mismo día con servicio de quimioterapia. Los borradores
    no cuentan como informe: el turno se lista marcado "Borrador".
"""
import os
from datetime import date, datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import exists, func, or_
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, joinedload

from auth.jwt import get_current_user
from database import get_db
from models.agenda import Agenda
from models.paciente import Paciente
from models.turno import Turno
from models.turno_estudio_archivo import TurnoEstudioArchivo
from models.turno_estudio_link import TurnoEstudioLink

router = APIRouter(prefix="/estudios", tags=["Estudios sin informe"])

TIPOS_POR_DEFECTO = "TOMOGRAFIA,ECOGRAFIA,ELECTRO_MAPEO,PET,CAMARA_GAMMA,QUIMIOTERAPIA"
INFORME_CERRADO = ("FINALIZADO", "RECTIFICADO")
MAX_FILAS = 2000
INICIO_CARGA_ESTUDIOS = date(2026, 11, 21)  # empezó la carga de link/PDF por turno
NO_DISPONIBLE = "La consulta de estudios sin informe no está disponible en este momento."


def tipos_estudio() -> list:
    raw = os.getenv("ESTUDIO_AGENDA_TIPOS") or TIPOS_POR_DEFECTO
    return [t.strip().upper() for t in raw.split(",") if t.strip()]


def _ids(valor) -> set:
    return {int(x.strip()) for x in str(valor).split(",") if x.strip().isdigit()}


def agendas_permitidas(db: Session, current_user: dict) -> Optional[set]:
    """None = sin restricción (ADMIN). Mismo criterio de permisos por agenda que /turnos."""
    if str(current_user.get("role") or "").upper() == "ADMIN":
        return None
    permitidas = None
    token_allowed = current_user.get("allowed_agendas")
    if token_allowed is not None:
        permitidas = _ids(token_allowed)
    from models.user import User
    db_user = None
    if current_user.get("id") is not None:
        db_user = db.get(User, current_user.get("id"))
    if not db_user and current_user.get("username"):
        db_user = db.query(User).filter(User.username == current_user.get("username")).first()
    if db_user:
        if db_user.allowed_agendas is not None:
            ids = _ids(db_user.allowed_agendas)
            permitidas = ids if permitidas is None else permitidas & ids
        if db_user.agendas:
            ids = {a.id for a in db_user.agendas}
            permitidas = ids if permitidas is None else permitidas & ids
    return permitidas


def _dia(valor):
    return valor.date() if isinstance(valor, datetime) else valor


def _hora(valor) -> str:
    return str(valor or "")[:5]


def _clave(paciente_id, agenda_id, fecha, hora) -> tuple:
    """Mismo paciente + mismo servicio + mismo día + mismo horario = un solo informe."""
    return (paciente_id, agenda_id, _dia(fecha), _hora(hora))


def _nombre_practicas(turno: Turno) -> str:
    nombres = [p.nombre for p in (turno.practicas or []) if p and p.nombre]
    if not nombres and turno.practica and turno.practica.nombre:
        nombres = [turno.practica.nombre]
    return ", ".join(nombres)


@router.get("/sin-informe")
def estudios_sin_informe(
    desde: Optional[date] = Query(default=None),
    hasta: Optional[date] = Query(default=None),
    agenda_id: Optional[int] = Query(default=None),
    q: Optional[str] = Query(default=None, max_length=100),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    hoy = date.today()
    hasta = hasta or hoy
    # Por defecto, desde el inicio de la carga de links/PDF en miagendam (21/11/2026),
    # sin superar el máximo de un año.
    desde = desde or max(INICIO_CARGA_ESTUDIOS, hasta - timedelta(days=365))
    if desde > hasta:
        raise HTTPException(422, "La fecha 'desde' no puede ser posterior a 'hasta'.")
    if (hasta - desde).days > 366:
        raise HTTPException(422, "El rango no puede superar un año.")

    tipos = tipos_estudio()
    permitidas = agendas_permitidas(db, current_user)

    try:
        agendas_q = db.query(Agenda).filter(func.upper(Agenda.tipo).in_(tipos))
        if permitidas is not None:
            agendas_q = agendas_q.filter(Agenda.id.in_(permitidas or {-1}))
        agendas = agendas_q.order_by(Agenda.nombre).all()
        ids_agendas = [a.id for a in agendas]
        if agenda_id is not None:
            if agenda_id not in ids_agendas:
                raise HTTPException(403, "No tiene permiso sobre esa agenda o no es de estudios.")
            ids_agendas = [agenda_id]

        query = (db.query(Turno)
                 .join(Paciente, Paciente.id == Turno.paciente_id)
                 .options(joinedload(Turno.paciente).joinedload(Paciente.obra_social),
                          joinedload(Turno.agenda), joinedload(Turno.practica),
                          joinedload(Turno.practicas), joinedload(Turno.medico_derivante))
                 .filter(Turno.agenda_id.in_(ids_agendas or [-1]))
                 .filter(Turno.fecha >= datetime.combine(desde, datetime.min.time()))
                 .filter(Turno.fecha <= datetime.combine(hasta, datetime.max.time()))
                 .filter(~exists().where(TurnoEstudioLink.turno_id == Turno.id))
                 .filter(~exists().where(TurnoEstudioArchivo.turno_id == Turno.id)))

        query = query.filter(func.upper(func.coalesce(Turno.estado, "")) == "COMPLETADO")

        texto = (q or "").strip()
        if texto:
            patron = f"%{texto}%"
            query = query.filter(or_(Paciente.dni.ilike(patron), Paciente.apellido.ilike(patron),
                                     Paciente.nombre.ilike(patron)))

        # Informe clínico: si está cerrado, el turno no se lista; si es borrador, se marca.
        borradores = set()
        import config
        if getattr(config, "ENABLE_CLINICAL_REPORTS", False):
            from models.informe_clinico import InformeClinico
            query = query.filter(~exists().where(
                (InformeClinico.turno_id == Turno.id)
                & func.upper(InformeClinico.estado).in_(INFORME_CERRADO)))

        turnos = query.order_by(Turno.fecha.asc(), Turno.hora.asc()).limit(MAX_FILAS + 1).all()
        truncado = len(turnos) > MAX_FILAS
        turnos = turnos[:MAX_FILAS]

        # Mismo paciente + servicio + día + horario lleva un solo informe: si cualquiera
        # de esos turnos ya tiene link, PDF o informe cerrado, el grupo cuenta como informado.
        grupos_informados = set()
        if turnos:
            pacientes_ids = {t.paciente_id for t in turnos}
            informados = (db.query(Turno.paciente_id, Turno.agenda_id, Turno.fecha, Turno.hora)
                          .filter(Turno.paciente_id.in_(pacientes_ids))
                          .filter(Turno.agenda_id.in_(ids_agendas or [-1]))
                          .filter(Turno.fecha >= datetime.combine(desde, datetime.min.time()))
                          .filter(Turno.fecha <= datetime.combine(hasta, datetime.max.time()))
                          .filter(or_(exists().where(TurnoEstudioLink.turno_id == Turno.id),
                                      exists().where(TurnoEstudioArchivo.turno_id == Turno.id))))
            filas_inf = informados.all()
            if getattr(config, "ENABLE_CLINICAL_REPORTS", False):
                from models.informe_clinico import InformeClinico
                filas_inf += (db.query(Turno.paciente_id, Turno.agenda_id, Turno.fecha, Turno.hora)
                              .join(InformeClinico, InformeClinico.turno_id == Turno.id)
                              .filter(Turno.paciente_id.in_(pacientes_ids))
                              .filter(Turno.agenda_id.in_(ids_agendas or [-1]))
                              .filter(Turno.fecha >= datetime.combine(desde, datetime.min.time()))
                              .filter(Turno.fecha <= datetime.combine(hasta, datetime.max.time()))
                              .filter(func.upper(InformeClinico.estado).in_(INFORME_CERRADO)).all())
            grupos_informados = {_clave(r[0], r[1], r[2], r[3]) for r in filas_inf}
            turnos = [t for t in turnos
                      if _clave(t.paciente_id, t.agenda_id, t.fecha, t.hora) not in grupos_informados]

        # Quimioterapia: también cuenta como informe la evolución FIRMADA del paciente
        # ese día con servicio de quimioterapia (la carga el oncólogo en historia clínica).
        quimio_borrador = set()
        ids_quimio = {a.id for a in agendas if str(a.tipo or "").upper() == "QUIMIOTERAPIA"}
        turnos_quimio = [t for t in turnos if t.agenda_id in ids_quimio]
        if turnos_quimio:
            from models.historia_clinica import HistoriaClinica
            notas = (db.query(HistoriaClinica.paciente_id, HistoriaClinica.fecha, HistoriaClinica.estado)
                     .filter(HistoriaClinica.paciente_id.in_({t.paciente_id for t in turnos_quimio}))
                     .filter(HistoriaClinica.servicio.ilike("%QUIMIO%"))
                     .filter(HistoriaClinica.fecha >= datetime.combine(desde, datetime.min.time()))
                     .filter(HistoriaClinica.fecha <= datetime.combine(hasta, datetime.max.time()))
                     .all())
            firmadas = {(n[0], _dia(n[1])) for n in notas if str(n[2] or "").upper() == "FIRMADO"}
            quimio_borrador = {(n[0], _dia(n[1])) for n in notas if str(n[2] or "").upper() == "BORRADOR"}
            turnos = [t for t in turnos
                      if not (t.agenda_id in ids_quimio and (t.paciente_id, _dia(t.fecha)) in firmadas)]

        if turnos and getattr(config, "ENABLE_CLINICAL_REPORTS", False):
            from models.informe_clinico import InformeClinico
            borradores = {r[0] for r in db.query(InformeClinico.turno_id)
                          .filter(InformeClinico.turno_id.in_([t.id for t in turnos])).all()}
        borradores |= {t.id for t in turnos
                       if t.agenda_id in ids_quimio and (t.paciente_id, _dia(t.fecha)) in quimio_borrador}
    except HTTPException:
        raise
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(503, NO_DISPONIBLE)

    # Una fila por paciente + servicio + día + horario (varios estudios = un informe).
    filas = []
    por_clave = {}
    por_agenda = {}
    for t in turnos:
        p = t.paciente
        fecha_t = _dia(t.fecha)
        clave = _clave(t.paciente_id, t.agenda_id, t.fecha, t.hora)
        fila = por_clave.get(clave)
        if fila is None:
            nombre_agenda = t.agenda.nombre if t.agenda else ""
            por_agenda[nombre_agenda] = por_agenda.get(nombre_agenda, 0) + 1
            fila = {
                "turno_id": t.id,
                "turnos_ids": [],
                "cantidad_turnos": 0,
                "fecha": fecha_t.isoformat() if fecha_t else None,
                "hora": (t.hora or "")[:5],
                "dias": (hoy - fecha_t).days if fecha_t else None,
                "agenda_id": t.agenda_id,
                "agenda": nombre_agenda,
                "practicas": "",
                "estado": (t.estado or "").upper(),
                "borrador": False,
                "paciente_id": p.id if p else None,
                "paciente": f"{p.apellido}, {p.nombre}" if p else "",
                "dni": p.dni if p else "",
                "celular": (p.celular or p.telefono or "") if p else "",
                "obra_social": p.obra_social.nombre if p and p.obra_social else "",
                "medico_derivante": t.medico_derivante.nombre if t.medico_derivante else "",
            }
            por_clave[clave] = fila
            filas.append(fila)
        fila["turnos_ids"].append(t.id)
        fila["cantidad_turnos"] += 1
        nombres = [n for n in (fila["practicas"].split(", ") if fila["practicas"] else [])]
        for n in _nombre_practicas(t).split(", "):
            if n and n not in nombres:
                nombres.append(n)
        fila["practicas"] = ", ".join(nombres)
        fila["borrador"] = fila["borrador"] or t.id in borradores
        if not fila["medico_derivante"] and t.medico_derivante:
            fila["medico_derivante"] = t.medico_derivante.nombre

    return {
        "desde": desde.isoformat(),
        "hasta": hasta.isoformat(),
        "total": len(filas),
        "truncado": truncado,
        "por_agenda": [{"agenda": k, "cantidad": v} for k, v in sorted(por_agenda.items())],
        "agendas": [{"id": a.id, "nombre": a.nombre, "tipo": a.tipo} for a in agendas],
        "items": filas,
    }
