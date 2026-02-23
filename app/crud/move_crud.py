"""
CRUD operations for Move model.
"""
from sqlalchemy.orm import Session
from typing import Optional, List
from uuid import UUID
from model.move import Move


def create_move(
    db: Session,
    game_id: UUID,
    player_id: UUID,
    player: str,
    position: int
) -> Move:
    """
    Create a new move in a game.
    
    Args:
        db: Database session
        game_id: UUID of the game
        player_id: UUID of the player making the move
        player: Player marker (X or O)
        position: Position on the board (1-9)
    
    Returns:
        Created Move object
    """
    db_move = Move(
        game_id=game_id,
        player_id=player_id,
        player=player,
        position=position
    )
    db.add(db_move)
    db.commit()
    db.refresh(db_move)
    return db_move


def get_move_by_id(db: Session, move_id: UUID) -> Optional[Move]:
    """
    Get a move by its ID.
    
    Args:
        db: Database session
        move_id: Move UUID
    
    Returns:
        Move object if found, None otherwise
    """
    return db.query(Move).filter(Move.id == move_id).first()


def get_moves_by_game(db: Session, game_id: UUID) -> List[Move]:
    """
    Get all moves for a specific game, ordered by creation time.
    
    Args:
        db: Database session
        game_id: Game UUID
    
    Returns:
        List of Move objects ordered chronologically
    """
    return db.query(Move).filter(
        Move.game_id == game_id
    ).order_by(Move.created_at).all()


def get_moves_by_player(
    db: Session,
    player_id: UUID,
    skip: int = 0,
    limit: int = 100
) -> List[Move]:
    """
    Get all moves made by a specific player.
    
    Args:
        db: Database session
        player_id: Player UUID
        skip: Number of records to skip
        limit: Maximum number of records to return
    
    Returns:
        List of Move objects
    """
    return db.query(Move).filter(
        Move.player_id == player_id
    ).order_by(Move.created_at.desc()).offset(skip).limit(limit).all()


def get_move_count_by_game(db: Session, game_id: UUID) -> int:
    """
    Get the total number of moves in a game.
    
    Args:
        db: Database session
        game_id: Game UUID
    
    Returns:
        Number of moves
    """
    return db.query(Move).filter(Move.game_id == game_id).count()


def delete_move(db: Session, move_id: UUID) -> bool:
    """
    Delete a move by ID.
    
    Args:
        db: Database session
        move_id: Move UUID
    
    Returns:
        True if deleted, False if move not found
    """
    move = get_move_by_id(db, move_id)
    if not move:
        return False
    
    db.delete(move)
    db.commit()
    return True


def delete_moves_by_game(db: Session, game_id: UUID) -> int:
    """
    Delete all moves for a specific game.
    
    Args:
        db: Database session
        game_id: Game UUID
    
    Returns:
        Number of moves deleted
    """
    count = db.query(Move).filter(Move.game_id == game_id).delete()
    db.commit()
    return count
