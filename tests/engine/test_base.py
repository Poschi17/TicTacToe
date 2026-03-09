from sqlalchemy.orm import DeclarativeBase

from engine import Base


def test_base_is_declarative_base():
	assert issubclass(Base, DeclarativeBase)


def test_base_has_metadata():
	assert Base.metadata is not None
