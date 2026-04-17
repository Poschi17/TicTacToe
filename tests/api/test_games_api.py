"""
API tests for game endpoints.
Tests game creation, retrieval, movement, joining, and deletion.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app import app
from app.engine import SessionLocal
from app.model import User
from app.crud import user_crud, game_crud


client = TestClient(app)


@pytest.fixture
def db_session():
    """Provide a test database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def user_one_data():
    """First test user data."""
    return {
        "username": "gameuser1",
        "email": "gameuser1@example.com",
        "password": "SecurePassword123"
    }


@pytest.fixture
def user_two_data():
    """Second test user data."""
    return {
        "username": "gameuser2",
        "email": "gameuser2@example.com",
        "password": "SecurePassword456"
    }


@pytest.fixture
def auth_token_user_one(user_one_data):
    """Get authentication token for user 1."""
    client.post("/auth/register", json=user_one_data)
    login_data = {
        "username": user_one_data["username"],
        "password": user_one_data["password"]
    }
    response = client.post("/auth/login", data=login_data)
    return response.json()["access_token"]


@pytest.fixture
def auth_token_user_two(user_two_data):
    """Get authentication token for user 2."""
    client.post("/auth/register", json=user_two_data)
    login_data = {
        "username": user_two_data["username"],
        "password": user_two_data["password"]
    }
    response = client.post("/auth/login", data=login_data)
    return response.json()["access_token"]


class TestGameCreation:
    """Tests for game creation endpoint."""
    
    def test_create_game_success(self, auth_token_user_one):
        """Test successful game creation."""
        headers = {"Authorization": f"Bearer {auth_token_user_one}"}
        response = client.post("/games", headers=headers)
        
        assert response.status_code == 201
        data = response.json()
        assert "id" in data
        assert data["status"] == "waiting"
        assert data["current_player"] == "X"
        assert data["player_x_id"] is not None
        assert data["player_o_id"] is None
        assert len(data["board_state"]) == 9
        assert data["board_state"] == "---------"  # Empty board
        assert data["winner"] is None
    
    def test_create_game_without_auth(self):
        """Test game creation without authentication."""
        response = client.post("/games")
        
        assert response.status_code == 403
    
    def test_create_game_with_invalid_token(self):
        """Test game creation with invalid token."""
        headers = {"Authorization": "Bearer invalid_token"}
        response = client.post("/games", headers=headers)
        
        assert response.status_code == 401
    
    def test_create_multiple_games(self, auth_token_user_one):
        """Test that a user can create multiple games."""
        headers = {"Authorization": f"Bearer {auth_token_user_one}"}
        
        # Create first game
        response1 = client.post("/games", headers=headers)
        assert response1.status_code == 201
        game1_id = response1.json()["id"]
        
        # Create second game
        response2 = client.post("/games", headers=headers)
        assert response2.status_code == 201
        game2_id = response2.json()["id"]
        
        # IDs should be different
        assert game1_id != game2_id


class TestGameRetrieval:
    """Tests for game retrieval endpoints."""
    
    def test_get_all_games(self, auth_token_user_one):
        """Test retrieving all games."""
        headers = {"Authorization": f"Bearer {auth_token_user_one}"}
        
        # Create some games
        client.post("/games", headers=headers)
        client.post("/games", headers=headers)
        
        response = client.get("/games", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 2
        for game in data:
            assert "id" in game
            assert "moves" in game
    
    def test_get_all_games_with_status_filter(self, auth_token_user_one, auth_token_user_two):
        """Test retrieving games filtered by status."""
        headers1 = {"Authorization": f"Bearer {auth_token_user_one}"}
        headers2 = {"Authorization": f"Bearer {auth_token_user_two}"}
        
        # Create a game
        game_response = client.post("/games", headers=headers1)
        game_id = game_response.json()["id"]
        
        # Filter by waiting status
        response = client.get("/games?status=waiting", headers=headers1)
        assert response.status_code == 200
        games = response.json()
        assert len(games) >= 1
        assert all(g["status"] == "waiting" for g in games)
        
        # Join the game to change status
        client.post(f"/games/{game_id}/join", headers=headers2)
        
        # Filter by ongoing status
        response_ongoing = client.get("/games?status=ongoing", headers=headers1)
        assert response_ongoing.status_code == 200
        ongoing_games = response_ongoing.json()
        assert any(g["id"] == game_id for g in ongoing_games)
    
    def test_get_game_by_id(self, auth_token_user_one):
        """Test retrieving a specific game by ID."""
        headers = {"Authorization": f"Bearer {auth_token_user_one}"}
        
        # Create a game
        create_response = client.post("/games", headers=headers)
        game_id = create_response.json()["id"]
        
        # Get the game
        response = client.get(f"/games/{game_id}", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == game_id
        assert data["status"] == "waiting"
        assert "moves" in data
    
    def test_get_game_not_found(self, auth_token_user_one):
        """Test retrieving non-existent game."""
        headers = {"Authorization": f"Bearer {auth_token_user_one}"}
        fake_uuid = "00000000-0000-0000-0000-000000000000"
        
        response = client.get(f"/games/{fake_uuid}", headers=headers)
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]
    
    def test_get_game_board(self, auth_token_user_one):
        """Test getting the game board visualization."""
        headers = {"Authorization": f"Bearer {auth_token_user_one}"}
        
        # Create a game
        create_response = client.post("/games", headers=headers)
        game_id = create_response.json()["id"]
        
        # Get board
        response = client.get(f"/games/{game_id}/board", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "board" in data
        assert len(data["board"]) == 3
        assert all(len(row) == 3 for row in data["board"])
    
    def test_get_my_games(self, auth_token_user_one, auth_token_user_two):
        """Test retrieving games for current user."""
        headers1 = {"Authorization": f"Bearer {auth_token_user_one}"}
        headers2 = {"Authorization": f"Bearer {auth_token_user_two}"}
        
        # User 1 creates games
        game1_response = client.post("/games", headers=headers1)
        game1_id = game1_response.json()["id"]
        
        game2_response = client.post("/games", headers=headers1)
        game2_id = game2_response.json()["id"]
        
        # User 2 joins one game
        client.post(f"/games/{game2_id}/join", headers=headers2)
        
        # Get user 1's games
        response1 = client.get("/games/user/me", headers=headers1)
        assert response1.status_code == 200
        user1_games = response1.json()
        assert len(user1_games) >= 2
        
        # Get user 2's games
        response2 = client.get("/games/user/me", headers=headers2)
        assert response2.status_code == 200
        user2_games = response2.json()
        assert len(user2_games) >= 1
        assert any(g["id"] == game2_id for g in user2_games)
    
    def test_get_my_games_requires_auth(self):
        """Test that getting my games requires authentication."""
        response = client.get("/games/user/me")
        
        assert response.status_code == 403


class TestJoinGame:
    """Tests for joining a game."""
    
    def test_join_game_success(self, auth_token_user_one, auth_token_user_two):
        """Test successfully joining a game."""
        headers1 = {"Authorization": f"Bearer {auth_token_user_one}"}
        headers2 = {"Authorization": f"Bearer {auth_token_user_two}"}
        
        # User 1 creates a game
        game_response = client.post("/games", headers=headers1)
        game_id = game_response.json()["id"]
        
        # User 2 joins the game
        response = client.post(f"/games/{game_id}/join", headers=headers2)
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == game_id
        assert data["status"] == "ongoing"
        assert data["current_player"] == "X"
        assert data["player_o_id"] is not None
    
    def test_join_game_already_has_player_o(self, auth_token_user_one, auth_token_user_two, user_one_data):
        """Test that a game cannot be joined twice."""
        headers1 = {"Authorization": f"Bearer {auth_token_user_one}"}
        headers2 = {"Authorization": f"Bearer {auth_token_user_two}"}
        
        # Create third user
        user_three_data = {
            "username": "gameuser3",
            "email": "gameuser3@example.com",
            "password": "SecurePassword789"
        }
        client.post("/auth/register", json=user_three_data)
        login_data = {
            "username": user_three_data["username"],
            "password": user_three_data["password"]
        }
        login_response = client.post("/auth/login", data=login_data)
        headers3 = {"Authorization": f"Bearer {login_response.json()['access_token']}"}
        
        # User 1 creates a game
        game_response = client.post("/games", headers=headers1)
        game_id = game_response.json()["id"]
        
        # User 2 joins
        client.post(f"/games/{game_id}/join", headers=headers2)
        
        # User 3 tries to join
        response = client.post(f"/games/{game_id}/join", headers=headers3)
        
        assert response.status_code == 400
        assert "Player O" in response.json()["detail"]
    
    def test_join_own_game(self, auth_token_user_one):
        """Test that a user cannot join their own game as Player O."""
        headers = {"Authorization": f"Bearer {auth_token_user_one}"}
        
        # Create a game
        game_response = client.post("/games", headers=headers)
        game_id = game_response.json()["id"]
        
        # Try to join own game
        response = client.post(f"/games/{game_id}/join", headers=headers)
        
        assert response.status_code == 400
        assert "own game" in response.json()["detail"]
    
    def test_join_game_not_found(self, auth_token_user_one):
        """Test joining non-existent game."""
        headers = {"Authorization": f"Bearer {auth_token_user_one}"}
        fake_uuid = "00000000-0000-0000-0000-000000000000"
        
        response = client.post(f"/games/{fake_uuid}/join", headers=headers)
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]
    
    def test_join_game_requires_auth(self):
        """Test that joining a game requires authentication."""
        fake_uuid = "00000000-0000-0000-0000-000000000000"
        response = client.post(f"/games/{fake_uuid}/join")
        
        assert response.status_code == 403


class TestGameMoves:
    """Tests for making moves in a game."""
    
    def test_make_move_success(self, auth_token_user_one, auth_token_user_two):
        """Test successfully making a move."""
        headers1 = {"Authorization": f"Bearer {auth_token_user_one}"}
        headers2 = {"Authorization": f"Bearer {auth_token_user_two}"}
        
        # Create and join game
        game_response = client.post("/games", headers=headers1)
        game_id = game_response.json()["id"]
        client.post(f"/games/{game_id}/join", headers=headers2)
        
        # Make a move
        response = client.put(f"/games/{game_id}/move/5", headers=headers1)
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == game_id
        board = data["board_state"]
        assert board[4] == "X"  # Position 5 is index 4
        assert data["current_player"] == "O"
    
    def test_make_move_invalid_position(self, auth_token_user_one, auth_token_user_two):
        """Test making move with invalid position."""
        headers1 = {"Authorization": f"Bearer {auth_token_user_one}"}
        headers2 = {"Authorization": f"Bearer {auth_token_user_two}"}
        
        # Create and join game
        game_response = client.post("/games", headers=headers1)
        game_id = game_response.json()["id"]
        client.post(f"/games/{game_id}/join", headers=headers2)
        
        # Try to move out of range
        response = client.put(f"/games/{game_id}/move/10", headers=headers1)
        
        assert response.status_code == 400
        assert "between 1 and 9" in response.json()["detail"]
    
    def test_make_move_on_non_existent_game(self, auth_token_user_one):
        """Test making move on non-existent game."""
        headers = {"Authorization": f"Bearer {auth_token_user_one}"}
        fake_uuid = "00000000-0000-0000-0000-000000000000"
        
        response = client.put(f"/games/{fake_uuid}/move/5", headers=headers)
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]
    
    def test_make_move_requires_auth(self):
        """Test that making move requires authentication."""
        fake_uuid = "00000000-0000-0000-0000-000000000000"
        response = client.put(f"/games/{fake_uuid}/move/5")
        
        assert response.status_code == 403
    
    def test_move_sequence_alternates_players(self, auth_token_user_one, auth_token_user_two):
        """Test that moves alternate between players."""
        headers1 = {"Authorization": f"Bearer {auth_token_user_one}"}
        headers2 = {"Authorization": f"Bearer {auth_token_user_two}"}
        
        # Create and join game
        game_response = client.post("/games", headers=headers1)
        game_id = game_response.json()["id"]
        client.post(f"/games/{game_id}/join", headers=headers2)
        
        # Move 1: User 1 (X)
        move1 = client.put(f"/games/{game_id}/move/1", headers=headers1)
        assert move1.json()["current_player"] == "O"
        
        # Move 2: User 2 (O)
        move2 = client.put(f"/games/{game_id}/move/2", headers=headers2)
        assert move2.json()["current_player"] == "X"
        
        # Move 3: User 1 (X)
        move3 = client.put(f"/games/{game_id}/move/3", headers=headers1)
        assert move3.json()["current_player"] == "O"
    
    def test_move_on_occupied_position(self, auth_token_user_one, auth_token_user_two):
        """Test that a position cannot be moved on twice."""
        headers1 = {"Authorization": f"Bearer {auth_token_user_one}"}
        headers2 = {"Authorization": f"Bearer {auth_token_user_two}"}
        
        # Create and join game
        game_response = client.post("/games", headers=headers1)
        game_id = game_response.json()["id"]
        client.post(f"/games/{game_id}/join", headers=headers2)
        
        # Make a move
        client.put(f"/games/{game_id}/move/5", headers=headers1)
        client.put(f"/games/{game_id}/move/1", headers=headers2)
        
        # Try to move on position 5 again
        response = client.put(f"/games/{game_id}/move/5", headers=headers1)
        
        assert response.status_code == 400


class TestGameDeletion:
    """Tests for deleting games."""
    
    def test_delete_game_success(self, auth_token_user_one):
        """Test successfully deleting a game."""
        headers = {"Authorization": f"Bearer {auth_token_user_one}"}
        
        # Create a game
        game_response = client.post("/games", headers=headers)
        game_id = game_response.json()["id"]
        
        # Delete the game
        response = client.delete(f"/games/{game_id}", headers=headers)
        
        assert response.status_code == 204
        
        # Verify it's deleted
        get_response = client.get(f"/games/{game_id}", headers=headers)
        assert get_response.status_code == 404
    
    def test_delete_nonexistent_game(self, auth_token_user_one):
        """Test deleting non-existent game."""
        headers = {"Authorization": f"Bearer {auth_token_user_one}"}
        fake_uuid = "00000000-0000-0000-0000-000000000000"
        
        response = client.delete(f"/games/{fake_uuid}", headers=headers)
        
        assert response.status_code == 404
    
    def test_delete_game_requires_auth(self):
        """Test that deleting game requires authentication."""
        fake_uuid = "00000000-0000-0000-0000-000000000000"
        response = client.delete(f"/games/{fake_uuid}")
        
        assert response.status_code == 403
    
    def test_delete_completed_games(self, auth_token_user_one):
        """Test deleting all completed games."""
        headers = {"Authorization": f"Bearer {auth_token_user_one}"}
        
        # Create a few games
        client.post("/games", headers=headers)
        client.post("/games", headers=headers)
        
        # Delete completed games
        response = client.delete("/games/completed/all", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "deleted_count" in data
        assert "message" in data


class TestGameIntegration:
    """Integration tests for complete game flow."""
    
    def test_complete_game_flow_with_moves(self, auth_token_user_one, auth_token_user_two):
        """Test a complete game flow: create, join, make moves."""
        headers1 = {"Authorization": f"Bearer {auth_token_user_one}"}
        headers2 = {"Authorization": f"Bearer {auth_token_user_two}"}
        
        # Step 1: Create game
        game_response = client.post("/games", headers=headers1)
        assert game_response.status_code == 201
        game_id = game_response.json()["id"]
        initial_board = game_response.json()["board_state"]
        assert initial_board == "---------"
        
        # Step 2: Check game in waiting status
        waiting_games = client.get(f"/games/{game_id}", headers=headers1)
        assert waiting_games.json()["status"] == "waiting"
        
        # Step 3: Join game
        join_response = client.post(f"/games/{game_id}/join", headers=headers2)
        assert join_response.status_code == 200
        assert join_response.json()["status"] == "ongoing"
        
        # Step 4: Make several moves
        moves_sequence = [1, 2, 3, 4, 5]
        for i, position in enumerate(moves_sequence):
            if i % 2 == 0:
                headers = headers1
            else:
                headers = headers2
            
            response = client.put(f"/games/{game_id}/move/{position}", headers=headers)
            assert response.status_code == 200
        
        # Step 5: Get final game state
        final_game = client.get(f"/games/{game_id}", headers=headers1)
        assert final_game.status_code == 200
        final_data = final_game.json()
        assert len(final_data["moves"]) == len(moves_sequence)
        assert final_data["moves"][0]["position"] == 1
