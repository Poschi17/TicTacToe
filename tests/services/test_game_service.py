import pytest

from services.game_service import GameService


def test_check_winner_rows():
	board = "XXX------"
	assert GameService.check_winner(board) == "X"


def test_check_winner_columns():
	board = "X--X--X--"
	assert GameService.check_winner(board) == "X"


def test_check_winner_diagonals():
	board = "X---X---X"
	assert GameService.check_winner(board) == "X"


def test_check_winner_none():
	board = "XOXOXOOXO"
	assert GameService.check_winner(board) is None


def test_check_draw_true():
	board = "XOXOXOOXO"
	assert GameService.check_draw(board) is True


def test_check_draw_false_when_winner_exists():
	board = "XXXOOO---"
	assert GameService.check_draw(board) is False


def test_is_valid_move_true():
	board = "XOX-O----"
	assert GameService.is_valid_move(board, 4) is True


def test_is_valid_move_false_out_of_bounds():
	board = "---------"
	assert GameService.is_valid_move(board, 0) is False
	assert GameService.is_valid_move(board, 10) is False


def test_is_valid_move_false_occupied():
	board = "X--------"
	assert GameService.is_valid_move(board, 1) is False


def test_make_move_happy_path():
	board = "---------"
	new_board = GameService.make_move(board, 5, "X")
	assert new_board == "----X----"


def test_make_move_invalid_raises():
	board = "X--------"
	with pytest.raises(ValueError):
		GameService.make_move(board, 1, "O")


def test_get_next_player():
	assert GameService.get_next_player("X") == "O"
	assert GameService.get_next_player("O") == "X"


def test_get_game_status_won():
	board = "XXXOO----"
	status, winner = GameService.get_game_status(board)
	assert status == "won"
	assert winner == "X"


def test_get_game_status_draw():
	board = "XOXOXOOXO"
	status, winner = GameService.get_game_status(board)
	assert status == "draw"
	assert winner is None


def test_get_game_status_ongoing():
	board = "XOX-O----"
	status, winner = GameService.get_game_status(board)
	assert status == "ongoing"
	assert winner is None


def test_display_board_format():
	board = "XO-" "-O-" "X--"
	output = GameService.display_board(board)
	assert "X | O | -" in output
	assert "- | O | -" in output
	assert "X | - | -" in output


def test_get_available_positions():
	board = "XOX-O----"
	assert GameService.get_available_positions(board) == [4, 6, 7, 8, 9]
