from __future__ import annotations

import sys
from pathlib import Path
import pytest
from sqlalchemy import text

# Add the project root directory to sys.path so imports work correctly
ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))


@pytest.fixture(scope="function", autouse=True)
def cleanup_database():
    """
    Clean up database before each test by deleting all data from tables.
    This ensures tests don't interfere with each other.
    """
    from app.engine import SessionLocal, engine, Base
    
    # Create a session
    db = SessionLocal()
    try:
        # Get all table names from Base metadata
        # Delete in reverse order to respect foreign key constraints
        for table in reversed(Base.metadata.sorted_tables):
            db.execute(text(f"DELETE FROM {table.name}"))
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"Warning: Could not clean up database: {e}")
    finally:
        db.close()
    
    yield
    
    # Optional: Clean up after test as well
    db = SessionLocal()
    try:
        for table in reversed(Base.metadata.sorted_tables):
            db.execute(text(f"DELETE FROM {table.name}"))
        db.commit()
    except Exception:
        db.rollback()
    finally:
        db.close()
