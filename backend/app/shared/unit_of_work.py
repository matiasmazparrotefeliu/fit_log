"""Unit of Work (Fase 1).

Coordina una sesión de SQLAlchemy y ofrece un único punto de commit/rollback
para los casos de uso de la capa `application`. Uso previsto:

    with UnitOfWork() as uow:
        repo = SomeRepository(uow.session)
        ...
        uow.commit()
"""

from types import TracebackType

from sqlalchemy.orm import Session, sessionmaker

from app.core.database import SessionLocal


class UnitOfWork:
    """Contexto transaccional sobre una sesión de SQLAlchemy."""

    def __init__(self, session_factory: sessionmaker[Session] = SessionLocal) -> None:
        self._session_factory = session_factory
        self.session: Session | None = None

    def __enter__(self) -> "UnitOfWork":
        self.session = self._session_factory()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        if self.session is None:
            return
        try:
            if exc_type is not None:
                self.session.rollback()
            else:
                self.session.commit()
        finally:
            self.session.close()
            self.session = None

    def commit(self) -> None:
        """Confirma la transacción actual."""
        if self.session is not None:
            self.session.commit()

    def rollback(self) -> None:
        """Revierte la transacción actual."""
        if self.session is not None:
            self.session.rollback()
