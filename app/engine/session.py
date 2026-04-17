"""
Database session management and engine configuration.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator
from app.config import env_str, env_bool

# Database connection URL
# Format: postgresql://user:password@host:port/database
DATABASE_URL = env_str("DATABASE_URL", "postgresql://admin:Kennwort1@localhost:5432/tictactoe")
DEBUG = env_bool("DEBUG", True)

# Create the SQLAlchemy engine
engine = create_engine(
    DATABASE_URL,
    echo=DEBUG,
    pool_pre_ping=True,  # Verify connections before using them
    pool_size=5,
    max_overflow=10
)

# Create SessionLocal class for database sessions
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


def get_db() -> Generator[Session, None, None]:
    """
    Dependency function that yields a database session.
    Automatically closes the session after use.
    
    Usage in FastAPI:
        @app.get("/endpoint")
        def endpoint(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """
    Initialize the database by creating all tables.
    Should be called on application startup.
    """
    from app.engine.base import Base
    Base.metadata.create_all(bind=engine)
