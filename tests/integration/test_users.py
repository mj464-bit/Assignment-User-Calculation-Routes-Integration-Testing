from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.user import User


class TestRegister:
    def test_register_success(self, client: TestClient, fake_user_payload):
        response = client.post("/users/register", json=fake_user_payload)
        assert response.status_code == 201
        body = response.json()
        assert body["username"] == fake_user_payload["username"]
        assert body["email"] == fake_user_payload["email"]
        assert body["is_active"] is True
        # password must never be echoed back
        assert "password" not in body
        assert "confirm_password" not in body

    def test_register_persists_to_database(
        self, client: TestClient, db_session: Session, fake_user_payload
    ):
        response = client.post("/users/register", json=fake_user_payload)
        assert response.status_code == 201

        user = db_session.query(User).filter(User.username == fake_user_payload["username"]).first()
        assert user is not None
        assert user.email == fake_user_payload["email"]
        # the stored password must be hashed, never plaintext
        assert user.password != fake_user_payload["password"]
        assert user.verify_password(fake_user_payload["password"])

    def test_register_duplicate_username_rejected(self, client: TestClient, fake_user_payload):
        client.post("/users/register", json=fake_user_payload)

        duplicate = dict(fake_user_payload)
        duplicate["email"] = "different_" + fake_user_payload["email"]
        response = client.post("/users/register", json=duplicate)

        assert response.status_code == 400
        assert "already exists" in response.json()["detail"]

    def test_register_duplicate_email_rejected(self, client: TestClient, fake_user_payload):
        client.post("/users/register", json=fake_user_payload)

        duplicate = dict(fake_user_payload)
        duplicate["username"] = fake_user_payload["username"] + "2"
        response = client.post("/users/register", json=duplicate)

        assert response.status_code == 400
        assert "already exists" in response.json()["detail"]

    def test_register_password_mismatch_rejected(self, client: TestClient, fake_user_payload):
        fake_user_payload["confirm_password"] = "SomethingElse123"
        response = client.post("/users/register", json=fake_user_payload)
        assert response.status_code == 422

    def test_register_weak_password_rejected(self, client: TestClient, fake_user_payload):
        fake_user_payload["password"] = "alllowercase1"
        fake_user_payload["confirm_password"] = "alllowercase1"
        response = client.post("/users/register", json=fake_user_payload)
        assert response.status_code == 422

    def test_register_invalid_email_rejected(self, client: TestClient, fake_user_payload):
        fake_user_payload["email"] = "not-an-email"
        response = client.post("/users/register", json=fake_user_payload)
        assert response.status_code == 422

    def test_register_missing_field_rejected(self, client: TestClient, fake_user_payload):
        del fake_user_payload["first_name"]
        response = client.post("/users/register", json=fake_user_payload)
        assert response.status_code == 422


class TestLogin:
    def test_login_with_username_succeeds(self, client: TestClient, registered_user):
        response = client.post(
            "/users/login",
            json={"username": registered_user["username"], "password": registered_user["password"]},
        )
        assert response.status_code == 200
        body = response.json()
        assert "access_token" in body
        assert body["token_type"] == "bearer"

    def test_login_with_email_succeeds(self, client: TestClient, registered_user):
        """User.authenticate() should accept an email in the `username` field too."""
        response = client.post(
            "/users/login",
            json={"username": registered_user["email"], "password": registered_user["password"]},
        )
        assert response.status_code == 200
        assert "access_token" in response.json()

    def test_login_wrong_password_rejected(self, client: TestClient, registered_user):
        response = client.post(
            "/users/login",
            json={"username": registered_user["username"], "password": "TotallyWrong123"},
        )
        assert response.status_code == 401

    def test_login_nonexistent_user_rejected(self, client: TestClient):
        response = client.post(
            "/users/login", json={"username": "no_such_user", "password": "WhateverPass1"}
        )
        assert response.status_code == 401

    def test_token_unlocks_protected_endpoint(self, client: TestClient, auth_headers):
        response = client.get("/calculations", headers=auth_headers)
        assert response.status_code == 200

    def test_no_token_blocked_from_protected_endpoint(self, client: TestClient):
        response = client.get("/calculations")
        assert response.status_code == 403  # HTTPBearer rejects a missing Authorization header
        
