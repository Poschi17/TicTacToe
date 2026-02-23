"""
Pydantic schemas (DTOs) for Game model.
"""
from pydantic import BaseModel, Field, ConfigDict
from uuid import UUID
from datetime import datetime
from typing import Optional, List


class GameBase(BaseModel):
    """Base Game schema."""
    pass


class GameCreate(BaseModel):
    """Schema for creating a new game."""
    player_x_id: Optional[UUID] = Field(None, description="Player X UUID (optional for anonymous games)")
    player_o_id: Optional[UUID] = Field(None, description="Player O UUID (optional for anonymous games)")


class GameResponse(BaseModel):
    """Schema for game response."""
    id: UUID
    player_x_id: Optional[UUID]
    player_o_id: Optional[UUID]
    current_player: str = Field(..., description="Current player (X or O)")
    status: str = Field(..., description="Game status: ongoing, won, draw")
    winner: Optional[str] = Field(None, description="Winner (X or O) if game is won")
    board_state: str = Field(..., description="Board state as 9-character string")
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class GameWithMoves(GameResponse):
    """Schema for game response with move history."""
    moves: List["MoveResponse"] = Field(default_factory=list, description="List of moves in chronological order")


class GameUpdate(BaseModel):
    """Schema for updating a game."""
    board_state: Optional[str] = Field(None, min_length=9, max_length=9)
    current_player: Optional[str] = Field(None, pattern="^[XO]$")
    status: Optional[str] = Field(None, pattern="^(ongoing|won|draw)$")
    winner: Optional[str] = Field(None, pattern="^[XO]$")


class BoardDisplay(BaseModel):
    """Schema for displaying the board in a readable format."""
    board: List[List[str]] = Field(..., description="3x3 board representation")
    
    @classmethod
    def from_board_state(cls, board_state: str) -> "BoardDisplay":
        """Convert board_state string to 3x3 array."""
        board = [
            [board_state[0], board_state[1], board_state[2]],
            [board_state[3], board_state[4], board_state[5]],
            [board_state[6], board_state[7], board_state[8]]
        ]
        return cls(board=board)


# Import MoveResponse for forward reference
from schema.moveDto import MoveResponse
GameWithMoves.model_rebuild()
