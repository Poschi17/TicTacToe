import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from uuid import UUID

from services import GameService
from services.game_service import GameValidationError, GameNotFoundError
from engine import Base
from crud import user_crud, game_crud


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


@pytest.fixture()
def db_session():
	engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
	Base.metadata.create_all(bind=engine)
	SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
	db = SessionLocal()
	try:
		yield db
	finally:
		db.close()


def test_create_game_for_user_sets_player_x_and_open_player_o(db_session):
	user = user_crud.create_user(db_session, "x_user", "x_user@example.com", "secret123")
	game = GameService.create_game_for_user(db_session, user.id)

	assert game.player_x_id == user.id
	assert game.player_o_id is None
	assert game.status == "waiting"


def test_join_game_as_player_o_happy_path(db_session):
	user_x = user_crud.create_user(db_session, "join_x", "join_x@example.com", "secret123")
	user_o = user_crud.create_user(db_session, "join_o", "join_o@example.com", "secret123")
	game = game_crud.create_game(db_session, player_x_id=user_x.id, player_o_id=None, status="waiting")

	joined = GameService.join_game_as_player_o(db_session, game.id, user_o.id)

	assert joined.player_o_id == user_o.id
	assert joined.status == "ongoing"


def test_join_game_as_player_o_rejects_own_game(db_session):
	user_x = user_crud.create_user(db_session, "self_x", "self_x@example.com", "secret123")
	game = game_crud.create_game(db_session, player_x_id=user_x.id, player_o_id=None, status="waiting")

	with pytest.raises(GameValidationError):
		GameService.join_game_as_player_o(db_session, game.id, user_x.id)


def test_join_game_as_player_o_rejects_when_slot_taken(db_session):
	user_x = user_crud.create_user(db_session, "taken_x", "taken_x@example.com", "secret123")
	user_o = user_crud.create_user(db_session, "taken_o", "taken_o@example.com", "secret123")
	other_user = user_crud.create_user(db_session, "taken_other", "taken_other@example.com", "secret123")
	game = game_crud.create_game(db_session, player_x_id=user_x.id, player_o_id=user_o.id, status="ongoing")

	with pytest.raises(GameValidationError):
		GameService.join_game_as_player_o(db_session, game.id, other_user.id)


def test_join_game_as_player_o_missing_game(db_session):
	user_o = user_crud.create_user(db_session, "missing_o", "missing_o@example.com", "secret123")

	with pytest.raises(GameNotFoundError):
		GameService.join_game_as_player_o(
			db_session,
			UUID("00000000-0000-0000-0000-000000000000"),
			user_o.id
		)


def test_join_game_as_player_o_rejects_non_waiting_status(db_session):
	user_x = user_crud.create_user(db_session, "status_x", "status_x@example.com", "secret123")
	user_o = user_crud.create_user(db_session, "status_o", "status_o@example.com", "secret123")
	game = game_crud.create_game(db_session, player_x_id=user_x.id, player_o_id=None, status="ongoing")

	with pytest.raises(GameValidationError):
		GameService.join_game_as_player_o(db_session, game.id, user_o.id)
