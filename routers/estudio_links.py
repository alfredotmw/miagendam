# routers/estudio_links.py
"""Carga del link al estudio publicado en Visual Médica (TAC, PET, ecografía).

Aislado del resto: tabla propia (turno_estudio_links) y router propio. No modifica
el modelo Turno ni las respuestas existentes de /turnos. Si la tabla todavía no
existe, estos endpoints responden 503 y el resto del sistema no se entera.
"""
import os
import urllib.parse
from datetime import datetime
from typing import Optional

import hashlib
import re

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import Response
from pydantic import BaseModel
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from auth.jwt import get_current_user
from database import get_db
from models.turno import Turno
from models.turno_estudio_link import TurnoEstudioLink
from models.turno_estudio_archivo import TurnoEstudioArchivo

router = APIRouter(prefix="/turnos", tags=["Link de estudio"])

ROLES_EDICION = ("ADMIN", "RECEPCION")
DOMINIOS_POR_DEFECTO = "visualmedica.com"
NO_DISPONIBLE = "La carga de links de estudio no está disponible en este momento."
PDF_NO_DISPONIBLE = "La carga de informes en PDF no está disponible en este momento."
PDF_MAX_BYTES = 15 * 1024 * 1024  # 15 MB


class LinkEstudioIn(BaseModel):
    link: Optional[str] = None


def _rol(current_user: dict) -> str:
    return str(current_user.get("role") or "").upper()


def _ids(valor) -> list:
    return [int(x.strip()) for x in str(valor).split(",") if x.strip().isdigit()]


def _verificar_agenda(db: Session, current_user: dict, turno: Turno) -> None:
    """Mismo criterio de permisos por agenda que usa el resto de /turnos."""
    if _rol(current_user) == "ADMIN":
        return
    token_allowed = current_user.get("allowed_agendas")
    if token_allowed is not None and turno.agenda_id not in _ids(token_allowed):
        raise HTTPException(403, "No tiene permiso sobre la agenda de este turno.")
    from models.user import User
    db_user = None
    if current_user.get("id") is not None:
        db_user = db.get(User, current_user.get("id"))
    if not db_user and current_user.get("username"):
        db_user = db.query(User).filter(User.username == current_user.get("username")).first()
    if db_user:
        if db_user.allowed_agendas is not None and turno.agenda_id not in _ids(db_user.allowed_agendas):
            raise HTTPException(403, "No tiene permiso sobre la agenda de este turno.")
        if db_user.agendas and turno.agenda_id not in {a.id for a in db_user.agendas}:
            raise HTTPException(403, "No tiene permiso sobre la agenda de este turno.")


def validar_link(raw: str) -> str:
    """Solo https, sin usuario/contraseña, puerto 443 y dominio habilitado."""
    link = (raw or "").strip()
    if len(link) > 500:
        raise HTTPException(422, "El link no puede superar los 500 caracteres.")
    if any(c.isspace() for c in link):
        raise HTTPException(422, "El link no puede contener espacios.")
    try:
        parsed = urllib.parse.urlparse(link)
        port = parsed.port
    except ValueError:
        raise HTTPException(422, "El link ingresado no es una URL válida.")
    if parsed.scheme.lower() != "https":
        raise HTTPException(422, "El link debe comenzar con https://")
    if parsed.username is not None or parsed.password is not None or "@" in (parsed.netloc or ""):
        raise HTTPException(422, "El link no puede incluir usuario ni contraseña.")
    if port is not None and port != 443:
        raise HTTPException(422, "El link no puede usar un puerto distinto de 443.")
    host = (parsed.hostname or "").lower()
    if not host:
        raise HTTPException(422, "El link ingresado no tiene un dominio válido.")
    dominios = [d.strip().lower().lstrip(".")
                for d in (os.getenv("STUDY_LINK_DOMAINS") or DOMINIOS_POR_DEFECTO).split(",")
                if d.strip().lstrip(".")]
    if not any(host == d or host.endswith("." + d) for d in dominios):
        raise HTTPException(422, "El link tiene que ser del portal de estudios (Visual Médica).")
    return link


def _pdf_info(db: Session, turno_id: int):
    """Metadatos del PDF sin traer el contenido. None si no hay; False si la tabla falta."""
    try:
        fila = (db.query(TurnoEstudioArchivo.nombre_archivo, TurnoEstudioArchivo.tamano_bytes,
                         TurnoEstudioArchivo.fecha_carga)
                .filter(TurnoEstudioArchivo.turno_id == turno_id).first())
    except SQLAlchemyError:
        db.rollback()
        return False
    if not fila:
        return None
    return {"nombre": fila.nombre_archivo, "tamano_bytes": fila.tamano_bytes,
            "fecha_carga": fila.fecha_carga.isoformat()}


def _respuesta(turno_id: int, fila: Optional[TurnoEstudioLink], current_user: dict,
               db: Optional[Session] = None) -> dict:
    pdf = _pdf_info(db, turno_id) if db is not None else None
    return {
        "turno_id": turno_id,
        "link": fila.url if fila else None,
        "fecha_carga": (fila.fecha_modificacion or fila.fecha_carga).isoformat() if fila else None,
        "pdf": pdf or None,
        "pdf_disponible": pdf is not False,
        "puede_editar": _rol(current_user) in ROLES_EDICION,
    }


def _turno(db: Session, turno_id: int) -> Turno:
    turno = db.get(Turno, turno_id)
    if not turno:
        raise HTTPException(404, "Turno no encontrado")
    return turno


@router.get("/{turno_id}/link-estudio")
def ver_link_estudio(turno_id: int, db: Session = Depends(get_db),
                     current_user: dict = Depends(get_current_user)):
    turno = _turno(db, turno_id)
    try:
        fila = db.query(TurnoEstudioLink).filter(TurnoEstudioLink.turno_id == turno.id).first()
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(503, NO_DISPONIBLE)
    return _respuesta(turno.id, fila, current_user, db)


@router.put("/{turno_id}/link-estudio")
def guardar_link_estudio(turno_id: int, payload: LinkEstudioIn, db: Session = Depends(get_db),
                         current_user: dict = Depends(get_current_user)):
    if _rol(current_user) not in ROLES_EDICION:
        raise HTTPException(403, "No tiene permisos para cargar el link del estudio.")
    turno = _turno(db, turno_id)
    _verificar_agenda(db, current_user, turno)
    nuevo = None if not (payload.link or "").strip() else validar_link(payload.link)
    try:
        fila = db.query(TurnoEstudioLink).filter(TurnoEstudioLink.turno_id == turno.id).first()
        if nuevo is None:
            if fila:
                db.delete(fila)
            fila = None
        elif fila:
            fila.url = nuevo
            fila.modificado_por_id = current_user.get("id")
            fila.fecha_modificacion = datetime.now()
        else:
            fila = TurnoEstudioLink(turno_id=turno.id, url=nuevo,
                                    cargado_por_id=current_user.get("id"),
                                    fecha_carga=datetime.now())
            db.add(fila)
        db.commit()
        if fila is not None:
            db.refresh(fila)
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(503, NO_DISPONIBLE)
    return _respuesta(turno.id, fila, current_user, db)


def _link_seguro(db: Session, turno_id: int):
    try:
        return db.query(TurnoEstudioLink).filter(TurnoEstudioLink.turno_id == turno_id).first()
    except SQLAlchemyError:
        db.rollback()
        return None


def _nombre_seguro(nombre: str) -> str:
    base = re.sub(r"[^\w\-. ]", "_", (nombre or "informe.pdf").strip())[:200] or "informe.pdf"
    return base if base.lower().endswith(".pdf") else base + ".pdf"


@router.post("/{turno_id}/informe-pdf")
async def subir_informe_pdf(turno_id: int, archivo: UploadFile = File(...),
                            db: Session = Depends(get_db),
                            current_user: dict = Depends(get_current_user)):
    if _rol(current_user) not in ROLES_EDICION:
        raise HTTPException(403, "No tiene permisos para cargar el informe.")
    turno = _turno(db, turno_id)
    _verificar_agenda(db, current_user, turno)
    contenido = await archivo.read(PDF_MAX_BYTES + 1)
    if len(contenido) > PDF_MAX_BYTES:
        raise HTTPException(413, "El PDF supera los 15 MB. Si es un electroencefalograma, cargá solo el informe.")
    if not contenido.startswith(b"%PDF-"):
        raise HTTPException(422, "El archivo tiene que ser un PDF.")
    try:
        fila = db.query(TurnoEstudioArchivo).filter(TurnoEstudioArchivo.turno_id == turno.id).first()
        if fila is None:
            fila = TurnoEstudioArchivo(turno_id=turno.id)
            db.add(fila)
        fila.nombre_archivo = _nombre_seguro(archivo.filename)
        fila.tamano_bytes = len(contenido)
        fila.sha256 = hashlib.sha256(contenido).hexdigest()
        fila.contenido = contenido
        fila.cargado_por_id = current_user.get("id")
        fila.fecha_carga = datetime.now()
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(503, PDF_NO_DISPONIBLE)
    return _respuesta(turno.id, _link_seguro(db, turno.id), current_user, db)


@router.get("/{turno_id}/informe-pdf")
def ver_informe_pdf(turno_id: int, db: Session = Depends(get_db),
                    current_user: dict = Depends(get_current_user)):
    turno = _turno(db, turno_id)
    try:
        fila = db.query(TurnoEstudioArchivo).filter(TurnoEstudioArchivo.turno_id == turno.id).first()
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(503, PDF_NO_DISPONIBLE)
    if not fila:
        raise HTTPException(404, "Este turno no tiene informe en PDF.")
    return Response(content=fila.contenido, media_type="application/pdf", headers={
        "Content-Disposition": 'inline; filename="' + fila.nombre_archivo.replace('"', "") + '"',
        "Cache-Control": "no-store", "X-Content-Type-Options": "nosniff"})


@router.delete("/{turno_id}/informe-pdf")
def quitar_informe_pdf(turno_id: int, db: Session = Depends(get_db),
                       current_user: dict = Depends(get_current_user)):
    if _rol(current_user) not in ROLES_EDICION:
        raise HTTPException(403, "No tiene permisos para quitar el informe.")
    turno = _turno(db, turno_id)
    _verificar_agenda(db, current_user, turno)
    try:
        db.query(TurnoEstudioArchivo).filter(TurnoEstudioArchivo.turno_id == turno.id).delete()
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(503, PDF_NO_DISPONIBLE)
    return _respuesta(turno.id, _link_seguro(db, turno.id), current_user, db)
