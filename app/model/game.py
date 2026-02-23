from typing import final, Optional
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, DateTime, ForeignKey
from datetime import datetime, timezone
from engine import Base
from uuid import UUID
import uuid

@final
class Game(Base):
    """
    Represents a game of Tic Tac Toe between two players, tracking the game state, current player, and outcome.
    """
    __tablename__ = "games"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    player_x_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("users.id"), nullable=True)
    player_o_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("users.id"), nullable=True)
    current_player: Mapped[str] = mapped_column(String(1), default="X", nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="ongoing", nullable=False)  # ongoing, won, draw
    winner: Mapped[Optional[str]] = mapped_column(String(1), nullable=True)  # X, O, or None
    board_state: Mapped[str] = mapped_column(String(9), default="---------", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    
    # Relationships
    player_x = relationship("User", foreign_keys=[player_x_id], back_populates="games_as_x")
    player_o = relationship("User", foreign_keys=[player_o_id], back_populates="games_as_o")
    moves = relationship("Move", back_populates="game", cascade="all, delete-orphan")
    
    