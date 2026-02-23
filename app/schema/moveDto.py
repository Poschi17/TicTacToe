"""
Pydantic schemas (DTOs) for Move model.
"""
from pydantic import BaseModel, Field, ConfigDict, field_validator
from uuid import UUID
from datetime import datetime
from typing import Optional


class MoveBase(BaseModel):
    """Base Move schema."""
    position: int = Field(..., ge=1, le=9, description="Position on the board (1-9)")


class MoveCreate(MoveBase):
    """Schema for creating a new move."""
    pass


class MoveResponse(MoveBase):
    """Schema for move response."""
    id: UUID
    game_id: UUID
    player_id: UUID
    player: str = Field(..., description="Player who made the move (X or O)")
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class MoveRequest(BaseModel):
    """Schema for making a move via API."""
    position: int = Field(..., ge=1, le=9, description="Position on the board (1-9)")
    
    @field_validator('position')
    @classmethod
    def validate_position(cls, v: int) -> int:
        """Validate position is between 1 and 9."""
        if not 1 <= v <= 9:
            raise ValueError("Position must be between 1 and 9")
        return v
