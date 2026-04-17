from __future__ import annotations

from uuid import UUID, uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.api import auth, games
from app.engine import Base, get_db
from app.crud import game_crud


@pytest.fixture()
def db_session_factory():
	engine = create_engine(
		"sqlite://",
		connect_args={"check_same_thread": False},
		poolclass=StaticPool,
	)
	Base.metadata.create_all(bind=engine)
	session_factory = sessionmaker(autocommit=False, autoflush=False, bind=engine)
	try:
		yield session_factory
	finally:
		Base.metadata.drop_all(bind=engine)
		engine.dispose()


@pytest.fixture()
def client(db_session_factory):
	app = FastAPI()
	app.include_router(auth.router)
	app.include_router(games.router)

	def override_get_db():
		db: Session = db_session_factory()
		try:
			yield db
		finally:
			db.close()

	app.dependency_overrides[get_db] = override_get_db

	with TestClient(app) as test_client:
		yield test_client


def _unique_user_payload(prefix: str = "user") -> dict[str, str]:
	suffix = uuid4().hex[:8]
	username = f"{prefix}_{suffix}"
	return {
		"username": username,
		"email": f"{username}@example.com",
		"password": "secret123",
	}


def _register_user(client: TestClient, prefix: str = "user") -> dict:
	payload = _unique_user_payload(prefix)
	response = client.post("/auth/register", json=payload)
	assert response.status_code == 201
	return {"payload": payload, "response": response.json()}


def _login_user(client: TestClient, username_or_email: str, password: str = "secret123") -> str:
	response = client.post(
		"/auth/login",
		data={"username": username_or_email, "password": password},
	)
	assert response.status_code == 200
	return response.json()["access_token"]


def _auth_headers(token: str) -> dict[str, str]:
	return {"Authorization": f"Bearer {token}"}


def _create_game(client: TestClient, token: str) -> dict:
	response = client.post("/games", headers=_auth_headers(token))
	assert response.status_code == 201
	return response.json()


class TestCreateAndJoinGame:
	def test_create_game_requires_authentication(self, client: TestClient):
		response = client.post("/games")

		assert response.status_code == 403
		assert response.json()["detail"] == "Not authenticated"

	def test_create_game_success_sets_waiting_state(self, client: TestClient):
		player_x = _register_user(client, "create_x")
		token_x = _login_user(client, player_x["payload"]["username"])

		response = client.post("/games", headers=_auth_headers(token_x))

		assert response.status_code == 201
		body = response.json()
		assert body["player_x_id"] == player_x["response"]["id"]
		assert body["player_o_id"] is None
		assert body["status"] == "waiting"
		assert body["current_player"] == "X"
		assert body["board_state"] == "---------"

	def test_join_game_success(self, client: TestClient):
		player_x = _register_user(client, "join_x")
		player_o = _register_user(client, "join_o")
		token_x = _login_user(client, player_x["payload"]["username"])
		token_o = _login_user(client, player_o["payload"]["username"])
		game = _create_game(client, token_x)

		response = client.post(f"/games/{game['id']}/join", headers=_auth_headers(token_o))

		assert response.status_code == 200
		body = response.json()
		assert body["player_o_id"] == player_o["response"]["id"]
		assert body["status"] == "ongoing"
		assert body["moves"] == []

	def test_join_game_own_game_returns_400(self, client: TestClient):
		player_x = _register_user(client, "join_self")
		token_x = _login_user(client, player_x["payload"]["username"])
		game = _create_game(client, token_x)

		response = client.post(f"/games/{game['id']}/join", headers=_auth_headers(token_x))

		assert response.status_code == 400
		assert response.json()["detail"] == "You cannot join your own game as Player O"

	def test_join_game_missing_game_returns_404(self, client: TestClient):
		player = _register_user(client, "join_missing")
		token = _login_user(client, player["payload"]["username"])

		response = client.post(
			"/games/00000000-0000-0000-0000-000000000000/join",
			headers=_auth_headers(token),
		)

		assert response.status_code == 404
		assert "not found" in response.json()["detail"]

	def test_join_game_already_taken_returns_400(self, client: TestClient):
		player_x = _register_user(client, "join_taken_x")
		player_o = _register_user(client, "join_taken_o")
		third_user = _register_user(client, "join_taken_third")
		token_x = _login_user(client, player_x["payload"]["username"])
		token_o = _login_user(client, player_o["payload"]["username"])
		token_third = _login_user(client, third_user["payload"]["username"])

		game = _create_game(client, token_x)
		first_join = client.post(f"/games/{game['id']}/join", headers=_auth_headers(token_o))
		assert first_join.status_code == 200

		second_join = client.post(f"/games/{game['id']}/join", headers=_auth_headers(token_third))
		assert second_join.status_code == 400
		assert second_join.json()["detail"] == "Game already has a Player O"


class TestGameReadEndpoints:
	def test_get_all_games_with_status_filter(self, client: TestClient):
		player_x = _register_user(client, "list_x")
		player_o = _register_user(client, "list_o")
		token_x = _login_user(client, player_x["payload"]["username"])
		token_o = _login_user(client, player_o["payload"]["username"])

		waiting_game = _create_game(client, token_x)
		ongoing_game = _create_game(client, token_o)
		join_response = client.post(
			f"/games/{ongoing_game['id']}/join",
			headers=_auth_headers(token_x),
		)
		assert join_response.status_code == 200

		all_games_response = client.get("/games", headers=_auth_headers(token_x))
		waiting_response = client.get("/games?status=waiting", headers=_auth_headers(token_x))
		ongoing_response = client.get("/games?status=ongoing", headers=_auth_headers(token_x))

		assert all_games_response.status_code == 200
		assert len(all_games_response.json()) == 2

		waiting_ids = {game["id"] for game in waiting_response.json()}
		ongoing_ids = {game["id"] for game in ongoing_response.json()}
		assert waiting_game["id"] in waiting_ids
		assert ongoing_game["id"] in ongoing_ids

	def test_get_game_by_id_not_found_returns_404(self, client: TestClient):
		user = _register_user(client, "game_get_missing")
		token = _login_user(client, user["payload"]["username"])

		response = client.get(
			"/games/00000000-0000-0000-0000-000000000000",
			headers=_auth_headers(token),
		)

		assert response.status_code == 404
		assert "not found" in response.json()["detail"]

	def test_get_game_board_success(self, client: TestClient):
		player_x = _register_user(client, "board_x")
		player_o = _register_user(client, "board_o")
		token_x = _login_user(client, player_x["payload"]["username"])
		token_o = _login_user(client, player_o["payload"]["username"])

		game = _create_game(client, token_x)
		join_response = client.post(f"/games/{game['id']}/join", headers=_auth_headers(token_o))
		assert join_response.status_code == 200

		move_response = client.put(f"/games/{game['id']}/move/1", headers=_auth_headers(token_x))
		assert move_response.status_code == 200

		board_response = client.get(f"/games/{game['id']}/board", headers=_auth_headers(token_x))
		assert board_response.status_code == 200
		board = board_response.json()["board"]
		assert board == [["X", "-", "-"], ["-", "-", "-"], ["-", "-", "-"]]

	def test_get_my_games_returns_only_games_for_current_user(self, client: TestClient):
		player_x = _register_user(client, "my_x")
		player_o = _register_user(client, "my_o")
		outsider = _register_user(client, "my_out")

		token_x = _login_user(client, player_x["payload"]["username"])
		token_o = _login_user(client, player_o["payload"]["username"])
		token_outsider = _login_user(client, outsider["payload"]["username"])

		game_for_x = _create_game(client, token_x)
		game_for_outsider = _create_game(client, token_outsider)

		join_response = client.post(
			f"/games/{game_for_x['id']}/join",
			headers=_auth_headers(token_o),
		)
		assert join_response.status_code == 200

		my_games_response = client.get("/games/user/me", headers=_auth_headers(token_x))
		assert my_games_response.status_code == 200
		game_ids = {game["id"] for game in my_games_response.json()}
		assert game_for_x["id"] in game_ids
		assert game_for_outsider["id"] not in game_ids


class TestMoveAndDeleteGame:
	def test_make_move_waiting_game_returns_400(self, client: TestClient):
		player_x = _register_user(client, "wait_move_x")
		token_x = _login_user(client, player_x["payload"]["username"])
		game = _create_game(client, token_x)

		response = client.put(f"/games/{game['id']}/move/1", headers=_auth_headers(token_x))

		assert response.status_code == 400
		assert response.json()["detail"] == "Game is waiting for a second player to join"

	def test_make_move_position_out_of_bounds_returns_400(self, client: TestClient):
		player_x = _register_user(client, "move_bounds_x")
		player_o = _register_user(client, "move_bounds_o")
		token_x = _login_user(client, player_x["payload"]["username"])
		token_o = _login_user(client, player_o["payload"]["username"])

		game = _create_game(client, token_x)
		join_response = client.post(f"/games/{game['id']}/join", headers=_auth_headers(token_o))
		assert join_response.status_code == 200

		response = client.put(f"/games/{game['id']}/move/10", headers=_auth_headers(token_x))

		assert response.status_code == 400
		assert response.json()["detail"] == "Position must be between 1 and 9"

	def test_make_move_wrong_turn_returns_400(self, client: TestClient):
		player_x = _register_user(client, "turn_x")
		player_o = _register_user(client, "turn_o")
		token_x = _login_user(client, player_x["payload"]["username"])
		token_o = _login_user(client, player_o["payload"]["username"])

		game = _create_game(client, token_x)
		join_response = client.post(f"/games/{game['id']}/join", headers=_auth_headers(token_o))
		assert join_response.status_code == 200

		first_move = client.put(f"/games/{game['id']}/move/1", headers=_auth_headers(token_x))
		assert first_move.status_code == 200

		wrong_turn_move = client.put(f"/games/{game['id']}/move/2", headers=_auth_headers(token_x))
		assert wrong_turn_move.status_code == 400
		assert wrong_turn_move.json()["detail"] == "It's not your turn (O's turn)"

	def test_make_move_success(self, client: TestClient):
		player_x = _register_user(client, "move_ok_x")
		player_o = _register_user(client, "move_ok_o")
		token_x = _login_user(client, player_x["payload"]["username"])
		token_o = _login_user(client, player_o["payload"]["username"])

		game = _create_game(client, token_x)
		join_response = client.post(f"/games/{game['id']}/join", headers=_auth_headers(token_o))
		assert join_response.status_code == 200

		response = client.put(f"/games/{game['id']}/move/5", headers=_auth_headers(token_x))

		assert response.status_code == 200
		body = response.json()
		assert body["board_state"] == "----X----"
		assert body["current_player"] == "O"
		assert len(body["moves"]) == 1
		assert body["moves"][0]["position"] == 5
		assert body["moves"][0]["player"] == "X"

	def test_delete_game_success_and_missing_returns_404(self, client: TestClient):
		player_x = _register_user(client, "delete_x")
		token_x = _login_user(client, player_x["payload"]["username"])
		game = _create_game(client, token_x)

		delete_response = client.delete(f"/games/{game['id']}", headers=_auth_headers(token_x))
		assert delete_response.status_code == 204

		delete_again = client.delete(f"/games/{game['id']}", headers=_auth_headers(token_x))
		assert delete_again.status_code == 404
		assert "not found" in delete_again.json()["detail"]

	def test_delete_completed_games_deletes_only_completed(self, client: TestClient, db_session_factory):
		player_x = _register_user(client, "delete_completed_x")
		token_x = _login_user(client, player_x["payload"]["username"])

		waiting_game = _create_game(client, token_x)
		completed_game = _create_game(client, token_x)

		db = db_session_factory()
		try:
			updated = game_crud.update_game_board(
				db=db,
				game_id=UUID(completed_game["id"]),
				board_state="XXXOO----",
				current_player="X",
				status="won",
				winner="X",
			)
			assert updated is not None
		finally:
			db.close()

		response = client.delete("/games/completed/all", headers=_auth_headers(token_x))

		assert response.status_code == 200
		assert response.json()["deleted_count"] == 1

		all_games = client.get("/games", headers=_auth_headers(token_x))
		assert all_games.status_code == 200
		remaining_ids = {game["id"] for game in all_games.json()}
		assert waiting_game["id"] in remaining_ids
		assert completed_game["id"] not in remaining_ids
