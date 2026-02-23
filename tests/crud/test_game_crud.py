import pytest
from uuid import UUID
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from engine.base import Base
from crud import game_crud
from services.game_service import GameService

# Ensure model metadata is registered
import model.game  # noqa: F401


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


def test_create_game_happy_path(db_session):
	game = game_crud.create_game(db_session)
	assert game is not None
	assert game.current_player == "X"
	assert game.status == "ongoing"
	assert game.board_state == "---------"


def test_get_game_by_id_not_found(db_session):
	game = game_crud.get_game_by_id(db_session, UUID("00000000-0000-0000-0000-000000000000"))
	assert game is None


def test_update_game_board_happy_path(db_session):
	game = game_crud.create_game(db_session)
	updated = game_crud.update_game_board(
		db_session,
		game_id=game.id,
		board_state="X--------",
		current_player="O",
		status="ongoing",
		winner=None
	)
	assert updated is not None
	assert updated.board_state == "X--------"
	assert updated.current_player == "O"


def test_update_game_board_not_found(db_session):
	updated = game_crud.update_game_board(
		db_session,
		game_id=UUID("00000000-0000-0000-0000-000000000000"),
		board_state="X--------",
		current_player="O",
		status="ongoing",
		winner=None
	)
	assert updated is None


def test_delete_game_not_found(db_session):
	deleted = game_crud.delete_game(db_session, UUID("00000000-0000-0000-0000-000000000000"))
	assert deleted is False


def test_delete_completed_games_only_removes_finished(db_session):
	ongoing = game_crud.create_game(db_session)
	won = game_crud.create_game(db_session)
	draw = game_crud.create_game(db_session)

	game_crud.update_game_board(
		db_session,
		game_id=won.id,
		board_state="XXXOO----",
		current_player="X",
		status="won",
		winner="X"
	)
	game_crud.update_game_board(
		db_session,
		game_id=draw.id,
		board_state="XOXOXOOXO",
		current_player="X",
		status="draw",
		winner=None
	)

	deleted_count = game_crud.delete_completed_games(db_session)
	assert deleted_count == 2
	assert game_crud.get_game_by_id(db_session, ongoing.id) is not None


def test_valid_move_then_update_board(db_session):
	game = game_crud.create_game(db_session)
	assert GameService.is_valid_move(game.board_state, 1) is True
	new_board = GameService.make_move(game.board_state, 1, "X")
	updated = game_crud.update_game_board(
		db_session,
		game_id=game.id,
		board_state=new_board,
		current_player="O"
	)
	assert updated is not None
	assert updated.board_state == "X--------"


def test_full_board_draw_status(db_session):
	game = game_crud.create_game(db_session)
	full_board = "XOXOXOOXO"
	status, winner = GameService.get_game_status(full_board)
	assert status == "draw"
	assert winner is None
	updated = game_crud.update_game_board(
		db_session,
		game_id=game.id,
		board_state=full_board,
		current_player="X",
		status=status,
		winner=winner
	)
	assert updated is not None
	assert updated.status == "draw"
