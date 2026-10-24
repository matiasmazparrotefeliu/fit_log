"""Tests de registro de usuario (POST /api/v1/auth/register)."""

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import verify_password
from app.modules.auth.infrastructure.models import UserModel

PASSWORD = "Password123!"


def _payload(**overrides):
    base = {
        "email": "new.runner@example.com",
        "password": PASSWORD,
        "full_name": "New Runner",
        "birth_date": "1990-05-10",
        "weight_kg": 70.5,
    }
    base.update(overrides)
    return base


def test_register_success(client):
    response = client.post("/api/v1/auth/register", json=_payload())

    assert response.status_code == 201
    body = response.json()
    assert body["email"] == "new.runner@example.com"
    assert body["full_name"] == "New Runner"
    assert body["role"] == "runner"
    assert "password_hash" not in body
    assert set(body) == {
        "id",
        "email",
        "full_name",
        "role",
        "birth_date",
        "weight_kg",
        "created_at",
    }


def test_register_duplicate_email(client):
    assert client.post("/api/v1/auth/register", json=_payload()).status_code == 201

    response = client.post("/api/v1/auth/register", json=_payload())

    assert response.status_code == 409
    assert response.json() == {"detail": "Email already registered"}


@pytest.mark.parametrize(
    "payload",
    [
        {"email": "not-an-email", "password": PASSWORD, "full_name": "X"},
        {"email": "ok@example.com", "password": "short", "full_name": "X"},
        {"email": "ok@example.com", "password": PASSWORD},
    ],
)
def test_register_invalid_payload(client, payload):
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 422


def test_register_hashes_password(client, db: Session):
    client.post("/api/v1/auth/register", json=_payload())

    model = db.scalar(
        select(UserModel).where(UserModel.email == "new.runner@example.com")
    )
    assert model is not None
    assert model.password_hash != PASSWORD
    assert verify_password(PASSWORD, model.password_hash)


def test_register_cannot_escalate_role(client):
    # El payload incluye role=admin; debe ignorarse y crear un runner.
    response = client.post(
        "/api/v1/auth/register",
        json=_payload(email="escalate@example.com", role="admin"),
    )

    assert response.status_code == 201
    assert response.json()["role"] == "runner"
