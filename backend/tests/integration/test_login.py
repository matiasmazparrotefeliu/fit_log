"""Tests de inicio de sesión y perfil propio (auth + /users/me)."""

from app.core.security import decode_access_token
from tests.conftest import DEFAULT_PASSWORD, auth_headers


def test_login_success(client, runner_user):
    response = client.post(
        "/api/v1/auth/login",
        json={"email": runner_user.email, "password": DEFAULT_PASSWORD},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert isinstance(body["access_token"], str)
    assert body["access_token"]


def test_login_wrong_password(client, runner_user):
    response = client.post(
        "/api/v1/auth/login",
        json={"email": runner_user.email, "password": "WrongPassword123!"},
    )

    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid email or password"}


def test_login_unknown_email(client):
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "nobody@example.com", "password": DEFAULT_PASSWORD},
    )

    assert response.status_code == 401


def test_token_claims(client, runner_user, runner_token):
    claims = decode_access_token(runner_token)

    assert claims["sub"] == str(runner_user.id)
    assert claims["role"] == "runner"
    assert "exp" in claims


def test_me_requires_token(client):
    response = client.get("/api/v1/users/me")
    assert response.status_code == 401


def test_me_with_token(client, runner_user, runner_token):
    response = client.get("/api/v1/users/me", headers=auth_headers(runner_token))

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == str(runner_user.id)
    assert body["email"] == runner_user.email
    assert body["role"] == "runner"
    assert "password_hash" not in body


def test_me_invalid_token(client):
    response = client.get(
        "/api/v1/users/me",
        headers={"Authorization": "Bearer not-a-real-token"},
    )
    assert response.status_code == 401


def test_update_me(client, runner_user, runner_token):
    response = client.patch(
        "/api/v1/users/me",
        headers=auth_headers(runner_token),
        json={"full_name": "Updated Name", "weight_kg": 68.25},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["full_name"] == "Updated Name"
    assert float(body["weight_kg"]) == 68.25
    assert body["email"] == runner_user.email
