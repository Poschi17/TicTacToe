"""
CRUD operations for Game model.
"""
from sqlalchemy.orm import Session
from typing import Optional, List
from uuid import UUID
from datetime import datetime, timezone
from model.game import Game


def create_game(
    db: Session,
    player_x_id: Optional[UUID] = None,
    player_o_id: Optional[UUID] = None
) -> Game:
    """
    Create a new game.
    
    Args:
        db: Database session
        player_x_id: Optional UUID of player X
        player_o_id: Optional UUID of player O
    
    Returns:
        Created Game object
    """
    db_game = Game(
        player_x_id=player_x_id,
        player_o_id=player_o_id,
        current_player="X",
        status="ongoing",
        board_state="---------"
    )
    db.add(db_game)
    db.commit()
    db.refresh(db_game)
    return db_game


def get_game_by_id(db: Session, game_id: UUID) -> Optional[Game]:
    """
    Get a game by its ID.
    
    Args:
        db: Database session
        game_id: Game UUID
    
    Returns:
        Game object if found, None otherwise
    """
    return db.query(Game).filter(Game.id == game_id).first()


def get_all_games(db: Session, skip: int = 0, limit: int = 100) -> List[Game]:
    """
    Get all games with pagination.
    
    Args:
        db: Database session
        skip: Number of records to skip
        limit: Maximum number of records to return
    
    Returns:
        List of Game objects
    """
    return db.query(Game).offset(skip).limit(limit).all()


def get_games_by_user(db: Session, user_id: UUID, skip: int = 0, limit: int = 100) -> List[Game]:
    """
    Get all games involving a specific user.
    
    Args:
        db: Database session
        user_id: User UUID
        skip: Number of records to skip
        limit: Maximum number of records to return
    
    Returns:
        List of Game objects
    """
    return db.query(Game).filter(
        (Game.player_x_id == user_id) | (Game.player_o_id == user_id)
    ).offset(skip).limit(limit).all()


def get_ongoing_games(db: Session, skip: int = 0, limit: int = 100) -> List[Game]:
    """
    Get all ongoing games.
    
    Args:
        db: Database session
        skip: Number of records to skip
        limit: Maximum number of records to return
    
    Returns:
        List of ongoing Game objects
    """
    return db.query(Game).filter(
        Game.status == "ongoing"
    ).offset(skip).limit(limit).all()


def update_game_board(
    db: Session,
    game_id: UUID,
    board_state: str,
    current_player: str,
    status: str = "ongoing",
    winner: Optional[str] = None
) -> Optional[Game]:
    """
    Update a game's board state and metadata.
    
    Args:
        db: Database session
        game_id: Game UUID
        board_state: New board state (9 characters)
        current_player: Current player (X or O)
        status: Game status (ongoing, won, draw)
        winner: Winner if game is won (X or O)
    
    Returns:
        Updated Game object if successful, None if game not found
    """
    game = get_game_by_id(db, game_id)
    if not game:
        return None
    
    game.board_state = board_state
    game.current_player = current_player
    game.status = status
    game.winner = winner
    game.updated_at = datetime.now(timezone.utc)
    
    db.commit()
    db.refresh(game)
    return game


def delete_game(db: Session, game_id: UUID) -> bool:
    """
    Delete a game by ID. This will also delete all associated moves due to cascade.
    
    Args:
        db: Database session
        game_id: Game UUID
    
    Returns:
        True if deleted, False if game not found
    """
    game = get_game_by_id(db, game_id)
    if not game:
        return False
    
    db.delete(game)
    db.commit()
    return True


def delete_completed_games(db: Session) -> int:
    """
    Delete all completed games (won or draw).
    
    Args:
        db: Database session
    
    Returns:
        Number of games deleted
    """
    count = db.query(Game).filter(
        (Game.status == "won") | (Game.status == "draw")
    ).delete()
    db.commit()
    return count
