import pytest
from uuid import UUID
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from engine.base import Base
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
	user = user_crud.create_user(db_session, "alice", "alice@example.com", "secret123")
	assert user is not None
	assert user.username == "alice"
	assert user.email == "alice@example.com"
	assert user.hashed_password != "secret123"


def test_create_user_duplicate_username_returns_none(db_session):
	user_crud.create_user(db_session, "alice", "alice@example.com", "secret123")
	user = user_crud.create_user(db_session, "alice", "alice2@example.com", "secret123")
	assert user is None


def test_create_user_duplicate_email_returns_none(db_session):
	user_crud.create_user(db_session, "alice", "alice@example.com", "secret123")
	user = user_crud.create_user(db_session, "bob", "alice@example.com", "secret123")
	assert user is None


def test_get_user_by_id_not_found(db_session):
	user = user_crud.get_user_by_id(db_session, UUID("00000000-0000-0000-0000-000000000000"))
	assert user is None


def test_get_user_by_username(db_session):
	user_crud.create_user(db_session, "alice", "alice@example.com", "secret123")
	user = user_crud.get_user_by_username(db_session, "alice")
	assert user is not None
	assert user.email == "alice@example.com"


def test_get_user_by_email(db_session):
	user_crud.create_user(db_session, "alice", "alice@example.com", "secret123")
	user = user_crud.get_user_by_email(db_session, "alice@example.com")
	assert user is not None
	assert user.username == "alice"


def test_get_all_users_pagination(db_session):
	user_crud.create_user(db_session, "alice", "alice@example.com", "secret123")
	user_crud.create_user(db_session, "bob", "bob@example.com", "secret123")
	users = user_crud.get_all_users(db_session, skip=0, limit=1)
	assert len(users) == 1


def test_authenticate_user_success(db_session):
	user_crud.create_user(db_session, "alice", "alice@example.com", "secret123")
	user = user_crud.authenticate_user(db_session, "alice", "secret123")
	assert user is not None


def test_authenticate_user_wrong_password(db_session):
	user_crud.create_user(db_session, "alice", "alice@example.com", "secret123")
	user = user_crud.authenticate_user(db_session, "alice", "wrong")
	assert user is None


def test_update_user_password(db_session):
	user = user_crud.create_user(db_session, "alice", "alice@example.com", "secret123")
	old_hash = user.hashed_password
	updated = user_crud.update_user_password(db_session, user.id, "newpass456")
	assert updated is not None
	assert updated.hashed_password != old_hash
	assert user_crud.authenticate_user(db_session, "alice", "newpass456") is not None


def test_delete_user(db_session):
	user = user_crud.create_user(db_session, "alice", "alice@example.com", "secret123")
	deleted = user_crud.delete_user(db_session, user.id)
	assert deleted is True
	assert user_crud.get_user_by_id(db_session, user.id) is None
