import pytest
from uuid import uuid4
from datetime import datetime, timezone

from schema.userDto import UserCreate, UserLogin, UserResponse, UserUpdate, Token, TokenData


def test_user_create_happy_path():
	user = UserCreate(username="alice", email="alice@example.com", password="secret123")
	assert user.username == "alice"
	assert user.email == "alice@example.com"


def test_user_create_invalid_email():
	with pytest.raises(ValueError):
		UserCreate(username="alice", email="not-an-email", password="secret123")


def test_user_create_short_password():
	with pytest.raises(ValueError):
		UserCreate(username="alice", email="alice@example.com", password="short")


def test_user_login_happy_path():
	login = UserLogin(username="alice", password="secret123")
	assert login.username == "alice"


def test_user_response_happy_path():
	now = datetime.now(timezone.utc)
	user = UserResponse(
		id=uuid4(),
		username="alice",
		email="alice@example.com",
		created_at=now
	)
	assert user.email == "alice@example.com"


def test_user_update_email_validates_lowercase():
	update = UserUpdate(email="Alice@Example.COM")
	assert update.email == "alice@example.com"


def test_user_update_invalid_email():
	with pytest.raises(ValueError):
		UserUpdate(email="bad-email")


def test_user_update_password_too_short():
	with pytest.raises(ValueError):
		UserUpdate(password="short")


def test_token_happy_path():
	token = Token(access_token="abc123", token_type="bearer")
	assert token.token_type == "bearer"


def test_token_data_happy_path():
	token_data = TokenData(username="alice", user_id=uuid4())
	assert token_data.username == "alice"
