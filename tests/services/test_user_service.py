import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import timedelta
from uuid import uuid4

from engine.base import Base
from services.user_service import UserService
from schema.userDto import UserCreate
from crud import user_crud

# Ensure model metadata is registered
import model.user  # noqa: F401


@pytest.fixture()
def db_session():
	engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
	Base.metadata.create_all(bind=engine)
	SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
	db = SessionLocal()
	try:
		yield db
	finally:
		db.close()


def test_create_user_happy_path(db_session):
	user_data = UserCreate(username="alice", email="alice@example.com", password="secret123")
	user = UserService.create_user(db_session, user_data)
	assert user is not None
	assert user.username == "alice"


def test_authenticate_user_success(db_session):
	user_crud.create_user(db_session, "alice", "alice@example.com", "secret123")
	user = UserService.authenticate_user(db_session, "alice", "secret123")
	assert user is not None
	assert user.username == "alice"


def test_authenticate_user_wrong_password(db_session):
	user_crud.create_user(db_session, "alice", "alice@example.com", "secret123")
	user = UserService.authenticate_user(db_session, "alice", "wrong")
	assert user is None


def test_create_and_verify_access_token():
	token = UserService.create_access_token(
		{"sub": "alice", "user_id": str(uuid4())},
		expires_delta=timedelta(minutes=5)
	)
	token_data = UserService.verify_token(token)
	assert token_data is not None
	assert token_data.username == "alice"


def test_verify_token_invalid_returns_none():
	token_data = UserService.verify_token("not-a-token")
	assert token_data is None


def test_get_current_user_happy_path(db_session):
	user = user_crud.create_user(db_session, "alice", "alice@example.com", "secret123")
	token = UserService.create_access_token({"sub": "alice", "user_id": str(user.id)})
	current_user = UserService.get_current_user(db_session, token)
	assert current_user is not None
	assert current_user.username == "alice"
