"""
Business logic service for Move operations.
Handles move validation and execution.
"""
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any
from uuid import UUID

from model.move import Move
from model.game import Game
from crud import move_crud, game_crud
from services.game_service import game_service


class MoveService:
    """Service class for move operations."""
    
    @staticmethod
    def validate_move(
        game: Game,
        position: int,
        player_id: UUID
    ) -> Optional[str]:
        """
        Validate if a move can be made.
        
        Args:
            game: Game object
            position: Position to place the mark (1-9)
            player_id: UUID of the player making the move
        
        Returns:
            Error message if invalid, None if valid
        """
        # Check if game is ongoing
        if game.status != 'ongoing':
            return f"Game is already finished with status: {game.status}"
        
        # Check if position is valid
        if not game_service.is_valid_move(game.board_state, position):
            return f"Position {position} is already occupied or out of bounds"
        
        # Determine which player should make the move
        if game.current_player == 'X' and game.player_x_id != player_id:
            return "It's not your turn (X's turn)"
        
        if game.current_player == 'O' and game.player_o_id != player_id:
            return "It's not your turn (O's turn)"
        
        return None
    
    @staticmethod
    def execute_move(
        db: Session,
        game: Game,
        position: int,
        player_id: UUID
    ) -> Dict[str, Any]:
        """
        Execute a move and update the game state.
        
        Args:
            db: Database session
            game: Game object
            position: Position to place the mark (1-9)
            player_id: UUID of the player making the move
        
        Returns:
            Dictionary with move result and updated game state
        
        Raises:
            ValueError: If move is invalid
        """
        # Validate move
        error = MoveService.validate_move(game, position, player_id)
        if error:
            raise ValueError(error)
        
        current_player = game.current_player
        
        # Make the move
        new_board_state = game_service.make_move(
            game.board_state,
            position,
            current_player
        )
        
        # Check game status
        status, winner = game_service.get_game_status(new_board_state)
        
        # Get next player
        next_player = game_service.get_next_player(current_player)
        
        # Create move record
        move = move_crud.create_move(
            db=db,
            game_id=game.id,
            player_id=player_id,
            player=current_player,
            position=position
        )
        
        # Update game
        updated_game = game_crud.update_game_board(
            db=db,
            game_id=game.id,
            board_state=new_board_state,
            current_player=next_player if status == 'ongoing' else current_player,
            status=status,
            winner=winner
        )
        
        return {
            "move": move,
            "game": updated_game,
            "status": status,
            "winner": winner,
            "message": MoveService._get_status_message(status, winner)
        }
    
    @staticmethod
    def _get_status_message(status: str, winner: Optional[str]) -> str:
        """Get a human-readable status message."""
        if status == 'won':
            return f"Player {winner} wins!"
        elif status == 'draw':
            return "It's a draw!"
        else:
            return "Move successful. Game continues."


# Create singleton instance
move_service = MoveService()
