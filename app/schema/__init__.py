"""
Pydantic schemas (DTOs) package for TicTacToe application.
"""
from schema.userDto import (
    UserBase,
    UserCreate,
    UserLogin,
    UserResponse,
    UserUpdate,
    Token,
    TokenData
)
from schema.gameDto import (
    GameBase,
    GameCreate,
    GameResponse,
    GameWithMoves,
    GameUpdate,
    BoardDisplay
)
from schema.moveDto import (
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
    "GameCreate",
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
