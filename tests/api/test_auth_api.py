from __future__ import annotations

from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.api import auth
from app.engine import Base, get_db


@pytest.fixture()
def db_session_factory():
	engine = create_engine(
		"sqlite://",
		connect_args={"check_same_thread": False},
		poolclass=StaticPool,
	)
	Base.metadata.create_all(bind=engine)
	session_factory = sessionmaker(autocommit=False, autoflush=False, bind=engine)
	try:
		yield session_factory
	finally:
		Base.metadata.drop_all(bind=engine)
		engine.dispose()


@pytest.fixture()
def client(db_session_factory):
	app = FastAPI()
	app.include_router(auth.router)

	def override_get_db():
		db: Session = db_session_factory()
		try:
			yield db
		finally:
			db.close()

	app.dependency_overrides[get_db] = override_get_db

	with TestClient(app) as test_client:
		yield test_client


def _unique_user_payload(prefix: str = "user") -> dict[str, str]:
	suffix = uuid4().hex[:8]
	username = f"{prefix}_{suffix}"
	return {
		"username": username,
		"email": f"{username}@example.com",
		"password": "secret123",
	}


def _register_user(client: TestClient, prefix: str = "user") -> dict:
	payload = _unique_user_payload(prefix)
	response = client.post("/auth/register", json=payload)
	assert response.status_code == 201
	body = response.json()
	return {"payload": payload, "response": body}


def _login_user(client: TestClient, username_or_email: str, password: str = "secret123") -> str:
	response = client.post(
		"/auth/login",
		data={"username": username_or_email, "password": password},
	)
	assert response.status_code == 200
	token = response.json()["access_token"]
	return token


def _auth_headers(token: str) -> dict[str, str]:
	return {"Authorization": f"Bearer {token}"}


class TestUserRegistration:
	def test_register_user_success(self, client: TestClient):
		payload = _unique_user_payload("register_ok")

		response = client.post("/auth/register", json=payload)

		assert response.status_code == 201
		body = response.json()
		assert body["username"] == payload["username"]
		assert body["email"] == payload["email"]
		assert "id" in body
		assert "created_at" in body

	def test_register_user_duplicate_username_returns_400(self, client: TestClient):
		first = _unique_user_payload("dup_user")
		second = {**_unique_user_payload("other"), "username": first["username"]}

		first_response = client.post("/auth/register", json=first)
		second_response = client.post("/auth/register", json=second)

		assert first_response.status_code == 201
		assert second_response.status_code == 400
		assert second_response.json()["detail"] == "Username already registered"

	def test_register_user_duplicate_email_returns_400(self, client: TestClient):
		first = _unique_user_payload("dup_email")
		second = {**_unique_user_payload("other"), "email": first["email"]}

		first_response = client.post("/auth/register", json=first)
		second_response = client.post("/auth/register", json=second)

		assert first_response.status_code == 201
		assert second_response.status_code == 400
		assert second_response.json()["detail"] == "Email already registered"


class TestUserLogin:
	def test_login_user_success_with_username(self, client: TestClient):
		created = _register_user(client, "login_name")

		response = client.post(
			"/auth/login",
			data={"username": created["payload"]["username"], "password": "secret123"},
		)

		assert response.status_code == 200
		body = response.json()
		assert body["token_type"] == "bearer"
		assert isinstance(body["access_token"], str)
		assert len(body["access_token"]) > 20

	def test_login_user_success_with_email(self, client: TestClient):
		created = _register_user(client, "login_email")

		response = client.post(
			"/auth/login",
			data={"username": created["payload"]["email"], "password": "secret123"},
		)

		assert response.status_code == 200
		assert response.json()["token_type"] == "bearer"

	def test_login_user_wrong_password_returns_401(self, client: TestClient):
		created = _register_user(client, "login_wrong_pw")

		response = client.post(
			"/auth/login",
			data={"username": created["payload"]["username"], "password": "wrong-password"},
		)

		assert response.status_code == 401
		assert response.json()["detail"] == "Incorrect username or password"
		assert response.headers.get("www-authenticate") == "Bearer"


class TestCurrentUser:
	def test_get_me_without_token_returns_403(self, client: TestClient):
		response = client.get("/auth/me")

		assert response.status_code == 403
		assert response.json()["detail"] == "Not authenticated"

	def test_get_me_with_invalid_token_returns_401(self, client: TestClient):
		response = client.get("/auth/me", headers=_auth_headers("invalid.jwt.token"))

		assert response.status_code == 401
		assert response.json()["detail"] == "Could not validate credentials"
		assert response.headers.get("www-authenticate") == "Bearer"

	def test_get_me_success(self, client: TestClient):
		created = _register_user(client, "me_ok")
		token = _login_user(client, created["payload"]["username"])

		response = client.get("/auth/me", headers=_auth_headers(token))

		assert response.status_code == 200
		body = response.json()
		assert body["id"] == created["response"]["id"]
		assert body["username"] == created["payload"]["username"]
		assert body["email"] == created["payload"]["email"]


class TestGetUserById:
	def test_get_user_by_id_requires_authentication(self, client: TestClient):
		created = _register_user(client, "target_user")

		response = client.get(f"/auth/users/{created['response']['id']}")

		assert response.status_code == 403
		assert response.json()["detail"] == "Not authenticated"

	def test_get_user_by_id_not_found_returns_404(self, client: TestClient):
		created = _register_user(client, "requester")
		token = _login_user(client, created["payload"]["username"])

		response = client.get(
			"/auth/users/00000000-0000-0000-0000-000000000000",
			headers=_auth_headers(token),
		)

		assert response.status_code == 404
		assert "not found" in response.json()["detail"]

	def test_get_user_by_id_success(self, client: TestClient):
		requester = _register_user(client, "requester_ok")
		target = _register_user(client, "target_ok")
		token = _login_user(client, requester["payload"]["username"])

		response = client.get(
			f"/auth/users/{target['response']['id']}",
			headers=_auth_headers(token),
		)

		assert response.status_code == 200
		body = response.json()
		assert body["id"] == target["response"]["id"]
		assert body["username"] == target["payload"]["username"]
		assert body["email"] == target["payload"]["email"]
