"""Implementación SQLAlchemy del puerto `UserRepository` (Fase 2)."""

import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.modules.auth.domain.entities import User, UserRole
from app.modules.auth.domain.ports import UserRepository
from app.modules.auth.infrastructure.models import UserModel


class SqlAlchemyUserRepository(UserRepository):
    """Repositorio de usuarios sobre una sesión SQLAlchemy."""

    def __init__(self, session: Session) -> None:
        self._session = session

    # ── Mapeo ORM → dominio ──────────────────────────────
    @staticmethod
    def _to_entity(model: UserModel) -> User:
        return User(
            id=model.id,
            email=model.email,
            password_hash=model.password_hash,
            full_name=model.full_name,
            role=UserRole(model.role),
            birth_date=model.birth_date,
            weight_kg=model.weight_kg,
            created_at=model.created_at,
        )

    # ── Lecturas ─────────────────────────────────────────
    def get_by_email(self, email: str) -> User | None:
        model = self._session.scalar(select(UserModel).where(UserModel.email == email))
        return self._to_entity(model) if model else None

    def get_by_id(self, user_id: uuid.UUID) -> User | None:
        model = self._session.get(UserModel, user_id)
        return self._to_entity(model) if model else None

    def exists_by_email(self, email: str) -> bool:
        count = self._session.scalar(
            select(func.count()).select_from(UserModel).where(UserModel.email == email)
        )
        return bool(count)

    def list(self, offset: int, limit: int) -> tuple[list[User], int]:
        total = self._session.scalar(select(func.count()).select_from(UserModel)) or 0
        rows = self._session.scalars(
            select(UserModel).order_by(UserModel.created_at).offset(offset).limit(limit)
        ).all()
        return [self._to_entity(row) for row in rows], int(total)

    # ── Escrituras ───────────────────────────────────────
    def create(
        self,
        *,
        email: str,
        password_hash: str,
        full_name: str,
        role: UserRole,
        birth_date: date | None,
        weight_kg: Decimal | None,
    ) -> User:
        model = UserModel(
            email=email,
            password_hash=password_hash,
            full_name=full_name,
            role=role.value,
            birth_date=birth_date,
            weight_kg=weight_kg,
        )
        self._session.add(model)
        self._session.commit()
        self._session.refresh(model)
        return self._to_entity(model)

    def update(self, user: User, **fields) -> User:
        model = self._session.get(UserModel, user.id)
        if model is None:
            return user

        for field, value in fields.items():
            if value is not None and hasattr(model, field):
                setattr(model, field, value)

        self._session.commit()
        self._session.refresh(model)
        return self._to_entity(model)
