import pytest
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.orm import sessionmaker, Mapped, mapped_column
from sqlalchemy import String

from engine.base import Base
import engine.session as session_module


@pytest.fixture()
def sqlite_session_module():
	engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
	SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
	session_module.engine = engine
	session_module.SessionLocal = SessionLocal
	return session_module


def test_get_db_yields_session(sqlite_session_module):
	db = next(sqlite_session_module.get_db())
	try:
		result = db.execute(text("SELECT 1")).scalar_one()
		assert result == 1
	finally:
		db.close()


def test_init_db_creates_tables(sqlite_session_module):
	class TempModel(Base):
		__tablename__ = "temp_test_table"
		id: Mapped[str] = mapped_column(String, primary_key=True)

	sqlite_session_module.init_db()
	inspector = inspect(sqlite_session_module.engine)
	assert "temp_test_table" in inspector.get_table_names()
