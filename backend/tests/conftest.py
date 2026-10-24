"""Configuración de la suite de tests (Fase 2).

Estrategia:
- PostgreSQL dedicado (`TEST_DATABASE_URL`, por defecto `fitlog_test`).
- La base se crea automáticamente si no existe (el usuario de Postgres es superuser).
- El esquema se crea desde `Base.metadata` (incluye los modelos importados).
- Antes de cada test se trunca `users` para aislar los casos.
- La dependencia `get_db` se sobrescribe con la sesión de test.
"""

from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine, make_url
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings
from app.core.database import Base, get_db
from app.core.security import hash_password
from app.main import app

# Importar modelos para registrarlos en Base.metadata.
from app.modules.auth.infrastructure.models import UserModel  # noqa: F401

DEFAULT_PASSWORD = "Password123!"


def _ensure_database(database_url: str) -> None:
    """Crea la base de test si no existe."""
    url = make_url(database_url)
    db_name = url.database
    if not db_name:
        raise RuntimeError("TEST_DATABASE_URL no define una base de datos")

    maintenance_url = url.set(database="postgres")
    maintenance_engine = create_engine(maintenance_url, isolation_level="AUTOCOMMIT")
    try:
        with maintenance_engine.connect() as conn:
            exists = conn.execute(
                text("SELECT 1 FROM pg_database WHERE datname = :name"),
                {"name": db_name},
            ).scalar()
            if not exists:
                conn.execute(text(f'CREATE DATABASE "{db_name}"'))
    finally:
        maintenance_engine.dispose()


@pytest.fixture(scope="session")
def engine() -> Generator[Engine, None, None]:
    """Motor de la base de test con el esquema creado."""
    _ensure_database(settings.test_database_url)
    test_engine = create_engine(settings.test_database_url, future=True)

    Base.metadata.create_all(bind=test_engine)
    yield test_engine
    Base.metadata.drop_all(bind=test_engine)
    test_engine.dispose()


@pytest.fixture(autouse=True)
def clean_tables(engine: Engine) -> Generator[None, None, None]:
    """Limpia todas las tablas del metadata antes de cada test."""
    tables = ", ".join(table.name for table in Base.metadata.sorted_tables)
    with engine.begin() as conn:
        if tables:
            conn.execute(text(f"TRUNCATE TABLE {tables} RESTART IDENTITY CASCADE"))
    yield


@pytest.fixture
def db(engine: Engine) -> Generator[Session, None, None]:
    """Sesión de SQLAlchemy contra la base de test."""
    testing_session = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    session = testing_session()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client(db: Session) -> Generator[TestClient, None, None]:
    """Cliente HTTP con `get_db` apuntando a la sesión de test."""

    def _override_get_db() -> Generator[Session, None, None]:
        yield db

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


# ── Helpers ──────────────────────────────────────────────
def create_user(db: Session, email: str, role: str) -> UserModel:
    """Inserta un usuario con la password por defecto."""
    model = UserModel(
        email=email,
        password_hash=hash_password(DEFAULT_PASSWORD),
        full_name="Test User",
        role=role,
    )
    db.add(model)
    db.commit()
    db.refresh(model)
    return model


def login(client: TestClient, email: str) -> str:
    """Inicia sesión y devuelve el access token."""
    response = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": DEFAULT_PASSWORD},
    )
    assert response.status_code == 200, response.text
    return response.json()["access_token"]


def auth_headers(token: str) -> dict[str, str]:
    """Construye el header Authorization."""
    return {"Authorization": f"Bearer {token}"}


# ── Fixtures de usuarios y tokens ────────────────────────
@pytest.fixture
def runner_user(db: Session) -> UserModel:
    return create_user(db, "runner@example.com", "runner")


@pytest.fixture
def admin_user(db: Session) -> UserModel:
    return create_user(db, "admin@example.com", "admin")


@pytest.fixture
def super_admin_user(db: Session) -> UserModel:
    return create_user(db, "super@example.com", "super_admin")


@pytest.fixture
def runner_token(client: TestClient, runner_user: UserModel) -> str:
    return login(client, runner_user.email)


@pytest.fixture
def admin_token(client: TestClient, admin_user: UserModel) -> str:
    return login(client, admin_user.email)


@pytest.fixture
def super_admin_token(client: TestClient, super_admin_user: UserModel) -> str:
    return login(client, super_admin_user.email)
