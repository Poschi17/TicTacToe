import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from engine.base import Base
from crud import game_crud
from services.game_service import GameService


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


def test_create_game_defaults(db_session):
	game = game_crud.create_game(db_session)
	assert game is not None
	assert game.current_player == "X"
	assert game.status == "ongoing"
	assert game.board_state == "---------"


def test_get_game_by_id(db_session):
	created = game_crud.create_game(db_session)
	fetched = game_crud.get_game_by_id(db_session, created.id)
	assert fetched is not None
	assert fetched.id == created.id


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
	assert updated.status == "ongoing"


def test_delete_game(db_session):
	game = game_crud.create_game(db_session)
	deleted = game_crud.delete_game(db_session, game.id)
	assert deleted is True
	assert game_crud.get_game_by_id(db_session, game.id) is None


def test_delete_completed_games(db_session):
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


def test_valid_move_updates_board():
	board = "---------"
	new_board = GameService.make_move(board, 1, "X")
	assert new_board == "X--------"


def test_invalid_move_occupied_position():
	board = "X--------"
	with pytest.raises(ValueError):
		GameService.make_move(board, 1, "O")


def test_full_board_draw():
	board = "XOXOXOOXO"
	status, winner = GameService.get_game_status(board)
	assert status == "draw"
	assert winner is None
