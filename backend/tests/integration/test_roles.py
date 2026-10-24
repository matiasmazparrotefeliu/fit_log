"""Tests de RBAC: runner/admin/super_admin sobre /users."""

from tests.conftest import auth_headers

USERS_URL = "/api/v1/users"


def _new_user_payload(email: str, role: str) -> dict:
    return {
        "email": email,
        "password": "Password123!",
        "full_name": "Created User",
        "role": role,
    }


def test_runner_cannot_list_users(client, runner_token):
    response = client.get(USERS_URL, headers=auth_headers(runner_token))
    assert response.status_code == 403


def test_admin_cannot_list_users(client, admin_token):
    response = client.get(USERS_URL, headers=auth_headers(admin_token))
    assert response.status_code == 403


def test_super_admin_can_list_users(client, super_admin_user, super_admin_token):
    response = client.get(USERS_URL, headers=auth_headers(super_admin_token))

    assert response.status_code == 200
    body = response.json()
    assert body["total"] >= 1
    assert body["page"] == 1
    assert body["size"] > 0
    assert body["pages"] >= 1
    assert any(item["email"] == super_admin_user.email for item in body["items"])
    assert all("password_hash" not in item for item in body["items"])


def test_runner_cannot_create_user(client, runner_token):
    response = client.post(
        USERS_URL,
        headers=auth_headers(runner_token),
        json=_new_user_payload("blocked.runner@example.com", "admin"),
    )
    assert response.status_code == 403


def test_admin_cannot_create_user(client, admin_token):
    response = client.post(
        USERS_URL,
        headers=auth_headers(admin_token),
        json=_new_user_payload("blocked.admin@example.com", "admin"),
    )
    assert response.status_code == 403


def test_super_admin_creates_admin(client, super_admin_token):
    response = client.post(
        USERS_URL,
        headers=auth_headers(super_admin_token),
        json=_new_user_payload("new.admin@example.com", "admin"),
    )

    assert response.status_code == 201
    body = response.json()
    assert body["email"] == "new.admin@example.com"
    assert body["role"] == "admin"


def test_super_admin_creates_runner(client, super_admin_token):
    response = client.post(
        USERS_URL,
        headers=auth_headers(super_admin_token),
        json=_new_user_payload("new.runner@example.com", "runner"),
    )

    assert response.status_code == 201
    assert response.json()["role"] == "runner"


def test_super_admin_cannot_create_super_admin(client, super_admin_token):
    response = client.post(
        USERS_URL,
        headers=auth_headers(super_admin_token),
        json=_new_user_payload("new.super@example.com", "super_admin"),
    )

    assert response.status_code == 422


def test_super_admin_create_duplicate_email(client, super_admin_token, admin_user):
    response = client.post(
        USERS_URL,
        headers=auth_headers(super_admin_token),
        json=_new_user_payload(admin_user.email, "runner"),
    )

    assert response.status_code == 409
    assert response.json() == {"detail": "Email already registered"}


def test_list_users_without_token(client):
    assert client.get(USERS_URL).status_code == 401


def test_list_users_invalid_token(client):
    response = client.get(
        USERS_URL,
        headers={"Authorization": "Bearer invalid-token"},
    )
    assert response.status_code == 401
