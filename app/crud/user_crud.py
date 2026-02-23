"""
CRUD operations for User model.
"""
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import Optional, List
from uuid import UUID
from model.user import User
import bcrypt


def get_password_hash(password: str) -> str:
    """Hash a password for storing."""
    # Convert password to bytes and hash it
    password_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a hashed password."""
    password_bytes = plain_password.encode('utf-8')
    hashed_bytes = hashed_password.encode('utf-8')
    return bcrypt.checkpw(password_bytes, hashed_bytes)


def create_user(db: Session, username: str, email: str, password: str) -> Optional[User]:
    """
    Create a new user with hashed password.
    
    Args:
        db: Database session
        username: Unique username
        email: Unique email
        password: Plain text password (will be hashed)
    
    Returns:
        User object if successful, None if username/email already exists
    """
    try:
        hashed_password = get_password_hash(password)
        db_user = User(
            username=username,
            email=email,
            hashed_password=hashed_password
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user
    except IntegrityError:
        db.rollback()
        return None


def get_user_by_id(db: Session, user_id: UUID) -> Optional[User]:
    """Get a user by their ID."""
    return db.query(User).filter(User.id == user_id).first()


def get_user_by_username(db: Session, username: str) -> Optional[User]:
    """Get a user by their username."""
    return db.query(User).filter(User.username == username).first()


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """Get a user by their email."""
    return db.query(User).filter(User.email == email).first()


def get_all_users(db: Session, skip: int = 0, limit: int = 100) -> List[User]:
    """
    Get all users with pagination.
    
    Args:
        db: Database session
        skip: Number of records to skip
        limit: Maximum number of records to return
    
    Returns:
        List of User objects
    """
    return db.query(User).offset(skip).limit(limit).all()


def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
    """
    Authenticate a user by username and password.
    
    Args:
        db: Database session
        username: Username
        password: Plain text password
    
    Returns:
        User object if authentication successful, None otherwise
    """
    user = get_user_by_username(db, username)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


def update_user_password(db: Session, user_id: UUID, new_password: str) -> Optional[User]:
    """
    Update a user's password.
    
    Args:
        db: Database session
        user_id: User ID
        new_password: New plain text password (will be hashed)
    
    Returns:
        Updated User object if successful, None if user not found
    """
    user = get_user_by_id(db, user_id)
    if not user:
        return None
    
    user.hashed_password = get_password_hash(new_password)
    db.commit()
    db.refresh(user)
    return user


def delete_user(db: Session, user_id: UUID) -> bool:
    """
    Delete a user by ID.
    
    Args:
        db: Database session
        user_id: User ID
    
    Returns:
        True if deleted, False if user not found
    """
    user = get_user_by_id(db, user_id)
    if not user:
        return False
    
    db.delete(user)
    db.commit()
    return True
