"""Tests del endpoint `POST /auth/super-admin` (bootstrap + delegación)."""

from tests.conftest import auth_headers

SUPER_ADMIN_URL = "/api/v1/auth/super-admin"


def _payload(email: str) -> dict:
    return {
        "email": email,
        "password": "Password123!",
        "full_name": "Super Admin",
    }


def test_bootstrap_crea_el_primer_super_admin(client):
    response = client.post(SUPER_ADMIN_URL, json=_payload("first.super@example.com"))

    assert response.status_code == 201
    body = response.json()
    assert body["email"] == "first.super@example.com"
    assert body["role"] == "super_admin"


def test_bootstrap_sin_token_rechazado_si_ya_existe(client, super_admin_user):
    response = client.post(SUPER_ADMIN_URL, json=_payload("other.super@example.com"))
    assert response.status_code == 403


def test_runner_no_puede_delegar_super_admin(client, super_admin_user, runner_token):
    response = client.post(
        SUPER_ADMIN_URL,
        headers=auth_headers(runner_token),
        json=_payload("delegated@example.com"),
    )
    assert response.status_code == 403


def test_super_admin_puede_delegar(client, super_admin_token):
    response = client.post(
        SUPER_ADMIN_URL,
        headers=auth_headers(super_admin_token),
        json=_payload("delegated@example.com"),
    )

    assert response.status_code == 201
    assert response.json()["role"] == "super_admin"


def test_email_duplicado(client, super_admin_user, super_admin_token):
    response = client.post(
        SUPER_ADMIN_URL,
        headers=auth_headers(super_admin_token),
        json=_payload(super_admin_user.email),
    )

    assert response.status_code == 409
    assert response.json() == {"detail": "Email already registered"}
