import pytest
from uuid import UUID
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from engine.base import Base
from crud import move_crud, game_crud, user_crud
from services.game_service import GameService

# Ensure models are registered
import model.user  # noqa: F401
import model.game  # noqa: F401
import model.move  # noqa: F401


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


@pytest.fixture()
def setup_game(db_session):
	user_x = user_crud.create_user(db_session, "playerx", "x@example.com", "secret123")
	user_o = user_crud.create_user(db_session, "playero", "o@example.com", "secret123")
	game = game_crud.create_game(db_session, player_x_id=user_x.id, player_o_id=user_o.id)
	return user_x, user_o, game


def test_create_move_happy_path(db_session, setup_game):
	user_x, _, game = setup_game
	move = move_crud.create_move(db_session, game.id, user_x.id, "X", 1)
	assert move is not None
	assert move.player == "X"
	assert move.position == 1


def test_get_move_by_id_not_found(db_session):
	move = move_crud.get_move_by_id(db_session, UUID("00000000-0000-0000-0000-000000000000"))
	assert move is None


def test_get_moves_by_game_ordered(db_session, setup_game):
	user_x, user_o, game = setup_game
	move_crud.create_move(db_session, game.id, user_x.id, "X", 1)
	move_crud.create_move(db_session, game.id, user_o.id, "O", 2)
	moves = move_crud.get_moves_by_game(db_session, game.id)
	assert [m.position for m in moves] == [1, 2]


def test_get_moves_by_player(db_session, setup_game):
	user_x, user_o, game = setup_game
	move_crud.create_move(db_session, game.id, user_x.id, "X", 1)
	move_crud.create_move(db_session, game.id, user_o.id, "O", 2)
	moves = move_crud.get_moves_by_player(db_session, user_x.id)
	assert len(moves) == 1
	assert moves[0].player_id == user_x.id


def test_get_move_count_by_game(db_session, setup_game):
	user_x, _, game = setup_game
	move_crud.create_move(db_session, game.id, user_x.id, "X", 1)
	move_crud.create_move(db_session, game.id, user_x.id, "X", 3)
	count = move_crud.get_move_count_by_game(db_session, game.id)
	assert count == 2


def test_delete_move(db_session, setup_game):
	user_x, _, game = setup_game
	move = move_crud.create_move(db_session, game.id, user_x.id, "X", 1)
	deleted = move_crud.delete_move(db_session, move.id)
	assert deleted is True
	assert move_crud.get_move_by_id(db_session, move.id) is None


def test_delete_moves_by_game(db_session, setup_game):
	user_x, _, game = setup_game
	move_crud.create_move(db_session, game.id, user_x.id, "X", 1)
	move_crud.create_move(db_session, game.id, user_x.id, "X", 2)
	deleted_count = move_crud.delete_moves_by_game(db_session, game.id)
	assert deleted_count == 2


def test_valid_move_updates_board(db_session, setup_game):
	user_x, _, game = setup_game
	new_board = GameService.make_move(game.board_state, 1, "X")
	updated = game_crud.update_game_board(
		db_session,
		game_id=game.id,
		board_state=new_board,
		current_player="O"
	)
	assert updated is not None
	assert updated.board_state == "X--------"


def test_full_board_draw_status(db_session, setup_game):
	_, _, game = setup_game
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
