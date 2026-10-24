"""Modelos SQLAlchemy del módulo auth (Fase 2)."""

from datetime import date
from decimal import Decimal

from sqlalchemy import CheckConstraint, Date, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.shared.base_entity import TimestampMixin, UUIDPKMixin


class UserModel(UUIDPKMixin, TimestampMixin, Base):
    """Tabla `users` (atletas / administradores)."""

    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint(
            "role IN ('runner', 'admin', 'super_admin')",
            name="ck_users_role",
        ),
    )

    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(100), nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False, server_default="runner")
    birth_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    weight_kg: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)

    def __repr__(self) -> str:  # pragma: no cover - debug
        return f"<UserModel {self.email} ({self.role})>"
