"""Control de acceso basado en roles — RBAC (Fase 2).

Roles del sistema: `runner`, `admin`, `super_admin`.

`get_current_principal` decodifica el JWT y construye un `Principal`
sin consultar la base de datos (claim-based). La resolución del usuario
completo contra la DB vive en `auth/presentation/dependencies.py`, para
mantener `core` independiente de los módulos de dominio.
"""

from dataclasses import dataclass

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError

from app.core.security import decode_access_token

_bearer_scheme = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class Principal:
    """Identidad mínima extraída del token (sin acceso a DB)."""

    user_id: str
    role: str


def get_current_principal(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
) -> Principal:
    """Dependencia: exige un Bearer token válido y devuelve el `Principal`."""
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = decode_access_token(credentials.credentials)
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload.get("sub")
    role = payload.get("role")
    if not user_id or not role:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return Principal(user_id=str(user_id), role=str(role))


def require_role(*roles: str):
    """Dependencia fabricada que exige que el rol esté en `roles`."""

    def _checker(principal: Principal = Depends(get_current_principal)) -> Principal:
        if principal.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        return principal

    return _checker
