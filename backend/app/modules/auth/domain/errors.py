"""Errores de dominio del módulo auth.

Se incorporan de forma incremental (no hay un `core/errors.py` global).
La capa presentation los traduce a respuestas HTTP.
"""


class AuthError(Exception):
    """Error base del módulo auth."""


class EmailAlreadyExists(AuthError):
    """El email ya está registrado."""


class InvalidCredentials(AuthError):
    """Email o contraseña incorrectos."""


class UserNotFound(AuthError):
    """No existe el usuario solicitado."""


class InvalidRoleAssignment(AuthError):
    """El rol solicitado no puede asignarse por esta vía."""
