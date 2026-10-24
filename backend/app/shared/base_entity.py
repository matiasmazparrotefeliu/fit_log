"""Entidades base compartidas por los modelos ORM (Fase 1).

Define mixins reutilizables:
- `UUIDPKMixin`: PK `id` UUID con `gen_random_uuid()`.
- `TimestampMixin`: `created_at` TIMESTAMPTZ con `CURRENT_TIMESTAMP`.

Los modelos de cada módulo los combinan, por ejemplo:

    from app.core.database import Base
    from app.shared.base_entity import UUIDPKMixin, TimestampMixin

    class User(UUIDPKMixin, TimestampMixin, Base):
        __tablename__ = "users"
        ...
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column


class UUIDPKMixin:
    """Mixin que agrega una PK `id` de tipo UUID."""

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid(),
    )


class TimestampMixin:
    """Mixin que agrega `created_at` con zona horaria."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.current_timestamp(),
        nullable=False,
    )
