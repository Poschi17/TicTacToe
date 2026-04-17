"""
Authentication API endpoints.
Handles user registration and login.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta
from uuid import UUID

from app.engine import get_db
from app.schema.userDto import UserCreate, UserResponse, UserLogin, Token
from app.services.user_service import user_service, ACCESS_TOKEN_EXPIRE_MINUTES
from app.crud import user_crud
from app.model.user import User

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


def get_current_user_dependency(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Dependency to get the current authenticated user.
    Use this in other endpoints that require authentication.
    Raises 403 Forbidden if no credentials are provided.
    """
    # Check if Authorization header is present
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authenticated",
        )
    
    # Extract token
    token = auth_header.replace("Bearer ", "")
    
    # Validate token and get user
    user = user_service.get_current_user(db, token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register_user(
    user_data: UserCreate,
    db: Session = Depends(get_db)
):
    """
    Register a new user.
    
    - **username**: Unique username (3-50 characters)
    - **email**: Valid email address
    - **password**: Password (minimum 8 characters)
    
    Returns the created user (without password).
    """
    # Check if username already exists
    existing_user = user_crud.get_user_by_username(db, user_data.username)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    # Check if email already exists
    existing_email = user_crud.get_user_by_email(db, user_data.email)
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create user
    user = user_service.create_user(db, user_data)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user"
        )
    
    return user


@router.post("/login", response_model=Token)
def login_user(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    Login with username or email and password.
    
    Returns a JWT access token.
    
    Use the token in subsequent requests:
    ```
    Authorization: Bearer <token>
    ```
    """
    # Authenticate user
    user = user_service.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = user_service.create_access_token(
        data={"sub": user.username, "user_id": str(user.id)},
        expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=UserResponse)
def get_current_user_info(
    current_user: User = Depends(get_current_user_dependency)
):
    """
    Get current authenticated user information.
    
    Requires authentication token (returns 403 if not provided).
    """
    return current_user


@router.get("/users/{user_id}", response_model=UserResponse)
def get_user_by_id(
    user_id: UUID,
    _current_user: User = Depends(get_current_user_dependency),
    db: Session = Depends(get_db)
):
    """
    Get a user by their ID.
    
    Requires authentication.
    
    - **user_id**: UUID of the user to retrieve
    """
    user = user_crud.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id {user_id} not found"
        )
    
    return user
