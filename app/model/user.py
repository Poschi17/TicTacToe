from typing import final
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, DateTime
from datetime import datetime, timezone
from engine import Base
from uuid import UUID, uuid4
import uuid

@final
class User(Base):
    """
    Represents a user in the system with their credentials and registration details.
    """
    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    
    # Relationships
    games_as_x = relationship("Game", foreign_keys="Game.player_x_id", back_populates="player_x")
    games_as_o = relationship("Game", foreign_keys="Game.player_o_id", back_populates="player_o")
    moves = relationship("Move", back_populates="player_user")
    