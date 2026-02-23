import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from engine.base import Base
from crud import game_crud, user_crud
from services.move_service import MoveService

# Ensure models are registered with SQLAlchemy metadata
import model.user
import model.game
import model.move


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
def users_and_game(db_session):
	user_x = user_crud.create_user(db_session, "playerx", "x@example.com", "secret123")
	user_o = user_crud.create_user(db_session, "playero", "o@example.com", "secret123")
	game = game_crud.create_game(db_session, player_x_id=user_x.id, player_o_id=user_o.id)
	return user_x, user_o, game


def test_validate_move_happy_path(users_and_game):
	user_x, _, game = users_and_game
	error = MoveService.validate_move(game, position=1, player_id=user_x.id)
	assert error is None


def test_validate_move_game_finished(users_and_game):
	user_x, _, game = users_and_game
	game.status = "won"
	error = MoveService.validate_move(game, position=1, player_id=user_x.id)
	assert error == "Game is already finished with status: won"


def test_validate_move_out_of_bounds(users_and_game):
	user_x, _, game = users_and_game
	error = MoveService.validate_move(game, position=10, player_id=user_x.id)
	assert error == "Position 10 is already occupied or out of bounds"


def test_validate_move_occupied(users_and_game):
	user_x, _, game = users_and_game
	game.board_state = "X--------"
	error = MoveService.validate_move(game, position=1, player_id=user_x.id)
	assert error == "Position 1 is already occupied or out of bounds"


def test_validate_move_wrong_turn(users_and_game):
	user_x, user_o, game = users_and_game
	game.current_player = "O"
	error = MoveService.validate_move(game, position=1, player_id=user_x.id)
	assert error == "It's not your turn (O's turn)"
	error = MoveService.validate_move(game, position=1, player_id=user_o.id)
	assert error is None


def test_execute_move_happy_path(db_session, users_and_game):
	user_x, _, game = users_and_game
	result = MoveService.execute_move(db_session, game, position=1, player_id=user_x.id)
	assert result["status"] == "ongoing"
	assert result["winner"] is None
	assert result["game"].board_state == "X--------"
	assert result["game"].current_player == "O"
	assert result["move"].position == 1
	assert result["move"].player == "X"


def test_execute_move_winning_move(db_session, users_and_game):
	user_x, _, game = users_and_game
	game.board_state = "XX-------"
	game.current_player = "X"
	result = MoveService.execute_move(db_session, game, position=3, player_id=user_x.id)
	assert result["status"] == "won"
	assert result["winner"] == "X"
	assert result["game"].board_state == "XXX------"
	assert result["game"].current_player == "X"


def test_execute_move_draw_last_move(db_session, users_and_game):
	_, user_o, game = users_and_game
	game.board_state = "XOXOXOOX-"
	game.current_player = "O"
	result = MoveService.execute_move(db_session, game, position=9, player_id=user_o.id)
	assert result["status"] == "draw"
	assert result["winner"] is None
	assert result["game"].board_state == "XOXOXOOXO"

