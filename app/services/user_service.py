"""
Business logic service for User operations.
Handles user authentication and management.
"""
from sqlalchemy.orm import Session
from typing import Optional
from uuid import UUID
from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt

from model.user import User
from crud import user_crud
from schema.userDto import UserCreate, TokenData

# JWT Configuration
SECRET_KEY = "your-secret-key-change-this-in-production"  # CHANGE THIS IN PRODUCTION!
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


class UserService:
    """Service class for user operations."""
    
    @staticmethod
    def create_user(db: Session, user_data: UserCreate) -> Optional[User]:
        """
        Create a new user.
        
        Args:
            db: Database session
            user_data: User creation data
        
        Returns:
            Created User object or None if username/email already exists
        """
        return user_crud.create_user(
            db=db,
            username=user_data.username,
            email=user_data.email,
            password=user_data.password
        )
    
    @staticmethod
    def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
        """
        Authenticate a user.
        
        Args:
            db: Database session
            username: Username
            password: Plain text password
        
        Returns:
            User object if authentication successful, None otherwise
        """
        return user_crud.authenticate_user(db, username, password)
    
    @staticmethod
    def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """
        Create a JWT access token.
        
        Args:
            data: Data to encode in the token
            expires_delta: Optional expiration time delta
        
        Returns:
            Encoded JWT token
        """
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    
    @staticmethod
    def verify_token(token: str) -> Optional[TokenData]:
        """
        Verify and decode a JWT token.
        
        Args:
            token: JWT token string
        
        Returns:
            TokenData if valid, None if invalid
        """
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            username: str = payload.get("sub")
            user_id: str = payload.get("user_id")
            
            if username is None:
                return None
            
            token_data = TokenData(username=username, user_id=UUID(user_id) if user_id else None)
            return token_data
        except JWTError:
            return None
    
    @staticmethod
    def get_current_user(db: Session, token: str) -> Optional[User]:
        """
        Get the current user from a JWT token.
        
        Args:
            db: Database session
            token: JWT token string
        
        Returns:
            User object if token is valid, None otherwise
        """
        token_data = UserService.verify_token(token)
        if token_data is None or token_data.username is None:
            return None
        
        user = user_crud.get_user_by_username(db, username=token_data.username)
        return user


# Create singleton instance
user_service = UserService()
