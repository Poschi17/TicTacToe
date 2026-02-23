from typing import final
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, DateTime, Integer, ForeignKey
from datetime import datetime
from engine import Base
from uuid import UUID
import uuid

@final
class Move(Base):
    """
    Represents a move in a game of Tic Tac Toe.
    """
    __tablename__ = "moves"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    game_id: Mapped[UUID] = mapped_column(ForeignKey("games.id", ondelete="CASCADE"), nullable=False)
    player_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    player: Mapped[str] = mapped_column(String(1), nullable=False)  # X or O
    position: Mapped[int] = mapped_column(Integer, nullable=False)  # 1-9
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    game = relationship("Game", back_populates="moves")
    player_user = relationship("User", back_populates="moves")
    
    