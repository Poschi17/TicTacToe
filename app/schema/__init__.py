"""
Pydantic schemas (DTOs) package for TicTacToe application.
"""
from app.schema.userDto import (
    UserBase,
    UserCreate,
    UserLogin,
    UserResponse,
    UserUpdate,
    Token,
    TokenData
)
from app.schema.gameDto import (
    GameBase,
    GameResponse,
    GameWithMoves,
    GameUpdate,
    BoardDisplay
)
from app.schema.moveDto import (
    MoveBase,
    MoveCreate,
    MoveResponse,
    MoveRequest
)

__all__ = [
    # User schemas
    "UserBase",
    "UserCreate",
    "UserLogin",
    "UserResponse",
    "UserUpdate",
    "Token",
    "TokenData",
    # Game schemas
    "GameBase",
    "GameResponse",
    "GameWithMoves",
    "GameUpdate",
    "BoardDisplay",
    # Move schemas
    "MoveBase",
    "MoveCreate",
    "MoveResponse",
    "MoveRequest"
]
