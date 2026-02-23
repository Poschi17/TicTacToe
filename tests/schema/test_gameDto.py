import pytest
from uuid import uuid4
from datetime import datetime, timezone

from schema.gameDto import GameResponse, GameUpdate, BoardDisplay, GameWithMoves
from schema.moveDto import MoveResponse


def test_game_response_happy_path():
	now = datetime.now(timezone.utc)
	game = GameResponse(
		id=uuid4(),
		player_x_id=uuid4(),
		player_o_id=uuid4(),
		current_player="X",
		status="ongoing",
		winner=None,
		board_state="---------",
		created_at=now,
		updated_at=now
	)
	assert game.status == "ongoing"
	assert game.board_state == "---------"


def test_game_update_valid_fields():
	update = GameUpdate(
		board_state="X--------",
		current_player="O",
		status="ongoing",
		winner=None
	)
	assert update.current_player == "O"


def test_game_update_invalid_status():
	with pytest.raises(ValueError):
		GameUpdate(status="finished")


def test_game_update_invalid_player():
	with pytest.raises(ValueError):
		GameUpdate(current_player="A")


def test_board_display_happy_path():
	board = BoardDisplay.from_board_state("XOX-O----")
	assert board.board == [
		["X", "O", "X"],
		["-", "O", "-"],
		["-", "-", "-"]
	]


def test_board_display_full_board():
	board = BoardDisplay.from_board_state("XOXOXOOXO")
	assert board.board == [
		["X", "O", "X"],
		["O", "X", "O"],
		["O", "X", "O"]
	]


def test_game_with_moves_default():
	now = datetime.now(timezone.utc)
	game = GameWithMoves(
		id=uuid4(),
		player_x_id=None,
		player_o_id=None,
		current_player="X",
		status="ongoing",
		winner=None,
		board_state="---------",
		created_at=now,
		updated_at=now,
		moves=[]
	)
	assert game.moves == []


def test_game_with_moves_includes_moves():
	now = datetime.now(timezone.utc)
	move = MoveResponse(
		id=uuid4(),
		game_id=uuid4(),
		player_id=uuid4(),
		player="X",
		position=1,
		created_at=now
	)
	game = GameWithMoves(
		id=uuid4(),
		player_x_id=None,
		player_o_id=None,
		current_player="O",
		status="ongoing",
		winner=None,
		board_state="X--------",
		created_at=now,
		updated_at=now,
		moves=[move]
	)
	assert len(game.moves) == 1
