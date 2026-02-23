"""
Game API endpoints.
Handles game creation, retrieval, and move execution.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID

from engine import get_db
from schema.gameDto import GameCreate, GameResponse, GameWithMoves, BoardDisplay
from schema.moveDto import MoveResponse
from model.user import User
from crud import game_crud, move_crud
from services.move_service import move_service
from api.auth import get_current_user_dependency

router = APIRouter(
    prefix="/games",
    tags=["Games"]
)


@router.post("", response_model=GameResponse, status_code=status.HTTP_201_CREATED)
def create_game(
    game_data: GameCreate,
    current_user: User = Depends(get_current_user_dependency),
    db: Session = Depends(get_db)
):
    """
    Create a new TicTacToe game.
    
    - **player_x_id**: Optional UUID of Player X (defaults to current user)
    - **player_o_id**: Optional UUID of Player O (can be set later or remain anonymous)
    
    The game starts with Player X's turn.
    """
    # Default player_x to current user if not specified
    player_x_id = game_data.player_x_id if game_data.player_x_id else current_user.id
    player_o_id = game_data.player_o_id
    
    # Create the game
    game = game_crud.create_game(
        db=db,
        player_x_id=player_x_id,
        player_o_id=player_o_id
    )
    
    return game


@router.get("", response_model=List[GameWithMoves])
def get_all_games(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    status: Optional[str] = Query(None, pattern="^(ongoing|won|draw)$", description="Filter by game status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_dependency)
):
    """
    Retrieve a list of all games with move histories and statuses.
    
    - **skip**: Number of records to skip (pagination)
    - **limit**: Maximum number of records to return (pagination)
    - **status**: Optional filter by game status (ongoing, won, draw)
    
    Returns games with complete move histories.
    """
    if status == "ongoing":
        games = game_crud.get_ongoing_games(db, skip, limit)
    else:
        games = game_crud.get_all_games(db, skip, limit)
        if status:
            games = [g for g in games if g.status == status]
    
    # Add moves to each game
    games_with_moves = []
    for game in games:
        moves = move_crud.get_moves_by_game(db, game.id)
        game_dict = GameResponse.model_validate(game).model_dump()
        game_dict['moves'] = moves
        games_with_moves.append(GameWithMoves(**game_dict))
    
    return games_with_moves


@router.get("/{game_id}", response_model=GameWithMoves)
def get_game_by_id(
    game_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_dependency)
):
    """
    Retrieve details of a specific game, including move history and status.
    
    - **game_id**: UUID of the game
    
    Returns the game with complete move history.
    """
    game = game_crud.get_game_by_id(db, game_id)
    if not game:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Game with id {game_id} not found"
        )
    
    # Get moves for this game
    moves = move_crud.get_moves_by_game(db, game.id)
    
    # Combine game and moves
    game_dict = GameResponse.model_validate(game).model_dump()
    game_dict['moves'] = moves
    
    return GameWithMoves(**game_dict)


@router.get("/{game_id}/board", response_model=BoardDisplay)
def get_game_board(
    game_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_dependency)
):
    """
    Get a visual representation of the game board.
    
    - **game_id**: UUID of the game
    
    Returns the board as a 3x3 array.
    """
    game = game_crud.get_game_by_id(db, game_id)
    if not game:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Game with id {game_id} not found"
        )
    
    return BoardDisplay.from_board_state(game.board_state)


@router.put("/{game_id}/move/{position}", response_model=GameWithMoves)
def make_move(
    game_id: UUID,
    position: int,
    current_user: User = Depends(get_current_user_dependency),
    db: Session = Depends(get_db)
):
    """
    Make a move at the specified position (1–9) in the given game.
    
    - **game_id**: UUID of the game
    - **position**: Position on the board (1-9)
    
    ```
    Board positions:
    1 | 2 | 3
    ---------
    4 | 5 | 6
    ---------
    7 | 8 | 9
    ```
    
    Returns the updated game with move history.
    
    **Errors:**
    - 404: Game not found
    - 400: Invalid move (position occupied, out of bounds, wrong turn, game finished)
    """
    # Validate position
    if not 1 <= position <= 9:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Position must be between 1 and 9"
        )
    
    # Get game
    game = game_crud.get_game_by_id(db, game_id)
    if not game:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Game with id {game_id} not found"
        )
    
    # Execute move
    try:
        result = move_service.execute_move(
            db=db,
            game=game,
            position=position,
            player_id=current_user.id
        )
        
        # Get updated game with moves
        updated_game = result["game"]
        moves = move_crud.get_moves_by_game(db, updated_game.id)
        
        game_dict = GameResponse.model_validate(updated_game).model_dump()
        game_dict['moves'] = moves
        
        return GameWithMoves(**game_dict)
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete("/{game_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_game(
    game_id: UUID,
    current_user: User = Depends(get_current_user_dependency),
    db: Session = Depends(get_db)
):
    """
    Delete a specific game.
    
    - **game_id**: UUID of the game
    
    This will also delete all associated moves (cascade delete).
    """
    success = game_crud.delete_game(db, game_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Game with id {game_id} not found"
        )
    
    return None


@router.delete("/completed/all", status_code=status.HTTP_200_OK)
def delete_completed_games(
    current_user: User = Depends(get_current_user_dependency),
    db: Session = Depends(get_db)
):
    """
    Delete all completed games (won or draw).
    
    Returns the number of games deleted.
    """
    count = game_crud.delete_completed_games(db)
    return {"deleted_count": count, "message": f"Deleted {count} completed game(s)"}


@router.get("/user/me", response_model=List[GameWithMoves])
def get_my_games(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user: User = Depends(get_current_user_dependency),
    db: Session = Depends(get_db)
):
    """
    Get all games for the current authenticated user.
    
    - **skip**: Number of records to skip (pagination)
    - **limit**: Maximum number of records to return (pagination)
    
    Returns games where the user is either Player X or Player O.
    """
    games = game_crud.get_games_by_user(db, current_user.id, skip, limit)
    
    # Add moves to each game
    games_with_moves = []
    for game in games:
        moves = move_crud.get_moves_by_game(db, game.id)
        game_dict = GameResponse.model_validate(game).model_dump()
        game_dict['moves'] = moves
        games_with_moves.append(GameWithMoves(**game_dict))
    
    return games_with_moves
