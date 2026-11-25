from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError

import os

# ⚙️ Configuración JWT
SECRET_KEY = os.getenv("SECRET_KEY", "supersecreto")  # ⚠️ en producción usar variable de entorno
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = 60

security = HTTPBearer()


# 🔑 Crear token de acceso
def create_access_token(data: dict, expires_minutes: int = ACCESS_TOKEN_EXPIRE_MINUTES) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=expires_minutes)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


# 🔍 Verificar token
def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """
    Verifica el token y retorna el payload (sub, role, exp).
    Lanza 401 si el token es inválido.
    """
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if "sub" not in payload or "role" not in payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token inválido: faltan campos requeridos",
            )
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o expirado",
        )


def get_current_user(payload: Dict[str, Any] = Depends(verify_token)) -> Dict[str, Any]:
    """
    Devuelve el usuario actual a partir del payload del JWT.
    Estructura: {"username": str, "role": str, "id": int}
    """
    return {
        "id": payload.get("id"),
        "username": payload["sub"], 
        "role": payload["role"],
        "allowed_agendas": payload.get("allowed_agendas")
    }


# 🔒 Requerir ciertos roles (ADMIN, RECEPCION, etc.)
def require_roles(allowed_roles: List[str]):
    """
    Dependencia para exigir ciertos roles en un endpoint.
    Ejemplo de uso:
        @router.post(..., dependencies=[Depends(require_roles(["ADMIN", "RECEPCION"]))])
    """
    def _require(current_user: Dict[str, Any] = Depends(get_current_user)):
        role = current_user.get("role")
        if role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Acceso denegado. Se requiere uno de estos roles: {allowed_roles}",
            )
        # 🔹 devolvemos el usuario autenticado
        return current_user
    return _require


# 🔒 Variante para enlaces/planillas externas: acepta "Authorization: Bearer ..."
# o ?token=... en la dirección (como /analytics/excel_feed y /radioterapia/feed).
from fastapi import Query as _Query
from fastapi.security import HTTPBearer as _HTTPBearer
_optional_security = _HTTPBearer(auto_error=False)


def _payload_from_token(token: str) -> Dict[str, Any]:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido o expirado")
    if "sub" not in payload or "role" not in payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido: faltan campos requeridos")
    return payload


def get_current_user_header_or_query(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_optional_security),
    token: Optional[str] = _Query(default=None, description="Token de sesión (alternativa al encabezado)"),
) -> Dict[str, Any]:
    raw = credentials.credentials if credentials else token
    if not raw:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Falta iniciar sesión")
    payload = _payload_from_token(raw)
    return {"id": payload.get("id"), "username": payload["sub"], "role": payload["role"],
            "allowed_agendas": payload.get("allowed_agendas")}


def require_admin(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    if str(current_user.get("role") or "").upper() != "ADMIN":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Solo administradores")
    return current_user
