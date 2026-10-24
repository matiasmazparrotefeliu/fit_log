"""Crea el primer usuario `super_admin` (bootstrap, Fase 2).

Uso:
    python -m scripts.create_super_admin --email admin@fitlog.local --password 'Secreta123!' --full-name 'Super Admin'

También acepta variables de entorno: SUPER_ADMIN_EMAIL, SUPER_ADMIN_PASSWORD,
SUPER_ADMIN_FULL_NAME.

Es idempotente: si el email ya existe, no lo duplica.
"""

import argparse
import os
import sys

from sqlalchemy import select

from app.core.database import SessionLocal
from app.core.security import hash_password
from app.modules.auth.domain.entities import UserRole
from app.modules.auth.infrastructure.models import UserModel


def main() -> int:
    parser = argparse.ArgumentParser(description="Crea el primer super_admin.")
    parser.add_argument("--email", default=os.getenv("SUPER_ADMIN_EMAIL"))
    parser.add_argument("--password", default=os.getenv("SUPER_ADMIN_PASSWORD"))
    parser.add_argument(
        "--full-name",
        default=os.getenv("SUPER_ADMIN_FULL_NAME", "Super Admin"),
    )
    args = parser.parse_args()

    if not args.email or not args.password:
        print(
            "Faltan credenciales. Usá --email/--password o SUPER_ADMIN_EMAIL/SUPER_ADMIN_PASSWORD.",
            file=sys.stderr,
        )
        return 2

    with SessionLocal() as session:
        existing = session.scalar(
            select(UserModel).where(UserModel.email == args.email)
        )
        if existing is not None:
            if existing.role != UserRole.SUPER_ADMIN.value:
                existing.role = UserRole.SUPER_ADMIN.value
                session.commit()
                print(f"Usuario existente actualizado a super_admin: {args.email}")
            else:
                print(f"El super_admin ya existe: {args.email}")
            return 0

        session.add(
            UserModel(
                email=args.email,
                password_hash=hash_password(args.password),
                full_name=args.full_name,
                role=UserRole.SUPER_ADMIN.value,
            )
        )
        session.commit()
        print(f"Super admin creado: {args.email}")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
