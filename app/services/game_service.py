"""
Business logic service for Game operations.
Contains TicTacToe game logic (win conditions, draw detection, etc.)
"""
from typing import Optional, Tuple, List
from uuid import UUID


class GameService:
    """Service class containing TicTacToe game logic."""
    
    # Win patterns (indices in board_state string)
    WIN_PATTERNS = [
        # Rows
        [0, 1, 2],
        [3, 4, 5],
        [6, 7, 8],
        # Columns
        [0, 3, 6],
        [1, 4, 7],
        [2, 5, 8],
        # Diagonals
        [0, 4, 8],
        [2, 4, 6]
    ]
    
    @staticmethod
    def check_winner(board_state: str) -> Optional[str]:
        """
        Check if there's a winner on the board.
        
        Args:
            board_state: 9-character string representing the board
        
        Returns:
            'X' if X won, 'O' if O won, None if no winner
        """
        for pattern in GameService.WIN_PATTERNS:
            positions = [board_state[i] for i in pattern]
            if positions[0] != '-' and positions[0] == positions[1] == positions[2]:
                return positions[0]
        return None
    
    @staticmethod
    def check_draw(board_state: str) -> bool:
        """
        Check if the game is a draw (board full, no winner).
        
        Args:
            board_state: 9-character string representing the board
        
        Returns:
            True if draw, False otherwise
        """
        return '-' not in board_state and GameService.check_winner(board_state) is None
    
    @staticmethod
    def is_valid_move(board_state: str, position: int) -> bool:
        """
        Check if a move is valid.
        
        Args:
            board_state: 9-character string representing the board
            position: Position to check (1-9)
        
        Returns:
            True if position is empty and within bounds, False otherwise
        """
        if not 1 <= position <= 9:
            return False
        index = position - 1
        return board_state[index] == '-'
    
    @staticmethod
    def make_move(board_state: str, position: int, player: str) -> str:
        """
        Make a move on the board.
        
        Args:
            board_state: Current 9-character board state
            position: Position to place the mark (1-9)
            player: Player making the move ('X' or 'O')
        
        Returns:
            New board state after the move
        
        Raises:
            ValueError: If move is invalid
        """
        if not GameService.is_valid_move(board_state, position):
            raise ValueError(f"Invalid move: Position {position} is already occupied or out of bounds")
        
        index = position - 1
        board_list = list(board_state)
        board_list[index] = player
        return ''.join(board_list)
    
    @staticmethod
    def get_next_player(current_player: str) -> str:
        """
        Get the next player.
        
        Args:
            current_player: Current player ('X' or 'O')
        
        Returns:
            Next player ('O' if current is 'X', 'X' if current is 'O')
        """
        return 'O' if current_player == 'X' else 'X'
    
    @staticmethod
    def get_game_status(board_state: str) -> Tuple[str, Optional[str]]:
        """
        Determine the game status and winner.
        
        Args:
            board_state: 9-character string representing the board
        
        Returns:
            Tuple of (status, winner) where:
            - status: 'ongoing', 'won', or 'draw'
            - winner: 'X', 'O', or None
        """
        winner = GameService.check_winner(board_state)
        if winner:
            return 'won', winner
        
        if GameService.check_draw(board_state):
            return 'draw', None
        
        return 'ongoing', None
    
    @staticmethod
    def display_board(board_state: str) -> str:
        """
        Create a visual representation of the board.
        
        Args:
            board_state: 9-character string representing the board
        
        Returns:
            Formatted board string for display
        """
        b = board_state
        return f"""
 {b[0]} | {b[1]} | {b[2]} 
-----------
 {b[3]} | {b[4]} | {b[5]} 
-----------
 {b[6]} | {b[7]} | {b[8]} 
"""
    
    @staticmethod
    def get_available_positions(board_state: str) -> List[int]:
        """
        Get all available positions on the board.
        
        Args:
            board_state: 9-character string representing the board
        
        Returns:
            List of available positions (1-9)
        """
        return [i + 1 for i, cell in enumerate(board_state) if cell == '-']


# Create singleton instance
game_service = GameService()
