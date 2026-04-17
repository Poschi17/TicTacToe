"""
API tests for user authentication endpoints.
Tests registration, login, token generation, and user retrieval.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app import app
from app.engine import get_db, SessionLocal
from app.model import User
from app.crud import user_crud


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
def test_user_data():
    """Test user data for registration and login."""
    return {
        "username": "testuser",
        "email": "testuser@example.com",
        "password": "SecurePassword123"
    }


@pytest.fixture
def test_user_two():
    """Second test user for testing multiple users."""
    return {
        "username": "testuser2",
        "email": "testuser2@example.com",
        "password": "SecurePassword456"
    }


@pytest.fixture
def registered_user(db_session, test_user_data):
    """Create a registered test user."""
    user = user_crud.create_user(
        db=db_session,
        username=test_user_data["username"],
        email=test_user_data["email"],
        password=test_user_data["password"]
    )
    return user, test_user_data


class TestUserRegistration:
    """Tests for user registration endpoint."""
    
    def test_register_user_success(self, test_user_data):
        """Test successful user registration."""
        response = client.post("/auth/register", json=test_user_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["username"] == test_user_data["username"]
        assert data["email"] == test_user_data["email"].lower()
        assert "id" in data
        assert "created_at" in data
        assert "password" not in data  # Password should not be in response
    
    def test_register_user_duplicate_username(self, test_user_data):
        """Test registration with duplicate username."""
        # Register first user
        response1 = client.post("/auth/register", json=test_user_data)
        assert response1.status_code == 201
        
        # Try to register with same username
        response2 = client.post("/auth/register", json=test_user_data)
        assert response2.status_code == 400
        assert "Username already registered" in response2.json()["detail"]
    
    def test_register_user_duplicate_email(self, test_user_data):
        """Test registration with duplicate email."""
        # Register first user
        response1 = client.post("/auth/register", json=test_user_data)
        assert response1.status_code == 201
        
        # Try to register with same email, different username
        user_data_dup_email = {
            "username": "different_username",
            "email": test_user_data["email"],
            "password": "AnotherPassword123"
        }
        response2 = client.post("/auth/register", json=user_data_dup_email)
        assert response2.status_code == 400
        assert "Email already registered" in response2.json()["detail"]
    
    def test_register_user_invalid_email(self):
        """Test registration with invalid email format."""
        invalid_data = {
            "username": "testuser",
            "email": "invalid-email",
            "password": "SecurePassword123"
        }
        response = client.post("/auth/register", json=invalid_data)
        assert response.status_code == 422
    
    def test_register_user_short_password(self):
        """Test registration with password too short."""
        invalid_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "Short1"
        }
        response = client.post("/auth/register", json=invalid_data)
        assert response.status_code == 422
    
    def test_register_user_short_username(self):
        """Test registration with username too short."""
        invalid_data = {
            "username": "ab",  # Too short
            "email": "test@example.com",
            "password": "SecurePassword123"
        }
        response = client.post("/auth/register", json=invalid_data)
        assert response.status_code == 422
    
    def test_register_user_long_username(self):
        """Test registration with username too long."""
        invalid_data = {
            "username": "a" * 51,  # Too long
            "email": "test@example.com",
            "password": "SecurePassword123"
        }
        response = client.post("/auth/register", json=invalid_data)
        assert response.status_code == 422
    
    def test_register_user_case_insensitive_email(self):
        """Test that email is converted to lowercase."""
        data = {
            "username": "testuser",
            "email": "TestUser@Example.COM",
            "password": "SecurePassword123"
        }
        response = client.post("/auth/register", json=data)
        assert response.status_code == 201
        assert response.json()["email"] == "testuser@example.com"


class TestUserLogin:
    """Tests for user login endpoint."""
    
    def test_login_user_success(self, test_user_data):
        """Test successful user login."""
        # Register user
        client.post("/auth/register", json=test_user_data)
        
        # Login
        login_data = {
            "username": test_user_data["username"],
            "password": test_user_data["password"]
        }
        response = client.post("/auth/login", data=login_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
    
    def test_login_with_wrong_password(self, test_user_data):
        """Test login with incorrect password."""
        # Register user
        client.post("/auth/register", json=test_user_data)
        
        # Login with wrong password
        login_data = {
            "username": test_user_data["username"],
            "password": "WrongPassword123"
        }
        response = client.post("/auth/login", data=login_data)
        
        assert response.status_code == 401
        assert "Incorrect username or password" in response.json()["detail"]
    
    def test_login_nonexistent_user(self):
        """Test login with non-existent user."""
        login_data = {
            "username": "nonexistent",
            "password": "SomePassword123"
        }
        response = client.post("/auth/login", data=login_data)
        
        assert response.status_code == 401
        assert "Incorrect username or password" in response.json()["detail"]
    
    def test_login_token_structure(self, test_user_data):
        """Test that returned token is valid JWT."""
        # Register and login
        client.post("/auth/register", json=test_user_data)
        login_data = {
            "username": test_user_data["username"],
            "password": test_user_data["password"]
        }
        response = client.post("/auth/login", data=login_data)
        token = response.json()["access_token"]
        
        # Token should be a non-empty string
        assert isinstance(token, str)
        assert len(token) > 0
        # Should be JWT format (three parts separated by dots)
        assert token.count(".") == 2


class TestUserInfo:
    """Tests for getting user information endpoints."""
    
    def test_get_current_user_success(self, test_user_data):
        """Test getting current authenticated user information."""
        # Register and login
        client.post("/auth/register", json=test_user_data)
        login_data = {
            "username": test_user_data["username"],
            "password": test_user_data["password"]
        }
        login_response = client.post("/auth/login", data=login_data)
        token = login_response.json()["access_token"]
        
        # Get current user info
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get("/auth/me", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == test_user_data["username"]
        assert data["email"] == test_user_data["email"].lower()
        assert "id" in data
        assert "created_at" in data
        assert "password" not in data
    
    def test_get_current_user_no_token(self):
        """Test getting current user without authentication."""
        response = client.get("/auth/me")
        
        assert response.status_code == 403
    
    def test_get_current_user_invalid_token(self):
        """Test getting current user with invalid token."""
        headers = {"Authorization": "Bearer invalid_token_123"}
        response = client.get("/auth/me", headers=headers)
        
        assert response.status_code == 401
    
    def test_get_current_user_expired_token(self, test_user_data):
        """Test getting current user with expired token."""
        # This would require mocking time or creating an actually expired token
        # For now, test with malformed token
        headers = {"Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.invalid.invalid"}
        response = client.get("/auth/me", headers=headers)
        
        assert response.status_code == 401
    
    def test_get_user_by_id_success(self, test_user_data, test_user_two):
        """Test getting user by ID."""
        # Register two users
        user1_response = client.post("/auth/register", json=test_user_data)
        user1_id = user1_response.json()["id"]
        
        client.post("/auth/register", json=test_user_two)
        
        # Login as first user
        login_data = {
            "username": test_user_data["username"],
            "password": test_user_data["password"]
        }
        login_response = client.post("/auth/login", data=login_data)
        token = login_response.json()["access_token"]
        
        # Get second user by ID
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get(f"/auth/users/{user1_id}", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == test_user_data["username"]
        assert data["id"] == user1_id
    
    def test_get_user_by_id_not_found(self, test_user_data):
        """Test getting non-existent user by ID."""
        # Register and login
        client.post("/auth/register", json=test_user_data)
        login_data = {
            "username": test_user_data["username"],
            "password": test_user_data["password"]
        }
        login_response = client.post("/auth/login", data=login_data)
        token = login_response.json()["access_token"]
        
        # Try to get non-existent user
        fake_uuid = "00000000-0000-0000-0000-000000000000"
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get(f"/auth/users/{fake_uuid}", headers=headers)
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]
    
    def test_get_user_by_id_requires_auth(self):
        """Test that getting user by ID requires authentication."""
        fake_uuid = "00000000-0000-0000-0000-000000000000"
        response = client.get(f"/auth/users/{fake_uuid}")
        
        assert response.status_code == 403


class TestAuthenticationFlow:
    """Integration tests for complete authentication flows."""
    
    def test_full_auth_flow(self, test_user_data):
        """Test complete authentication flow: register -> login -> get info."""
        # Step 1: Register
        register_response = client.post("/auth/register", json=test_user_data)
        assert register_response.status_code == 201
        user_id = register_response.json()["id"]
        
        # Step 2: Login
        login_data = {
            "username": test_user_data["username"],
            "password": test_user_data["password"]
        }
        login_response = client.post("/auth/login", data=login_data)
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]
        
        # Step 3: Get user info
        headers = {"Authorization": f"Bearer {token}"}
        me_response = client.get("/auth/me", headers=headers)
        assert me_response.status_code == 200
        assert me_response.json()["id"] == user_id
        
        # Step 4: Get specific user
        user_response = client.get(f"/auth/users/{user_id}", headers=headers)
        assert user_response.status_code == 200
        assert user_response.json()["username"] == test_user_data["username"]
    
    def test_multiple_users_isolation(self, test_user_data, test_user_two):
        """Test that different users are properly isolated."""
        # Register and login as user 1
        user1_reg = client.post("/auth/register", json=test_user_data)
        user1_id = user1_reg.json()["id"]
        
        login_data = {
            "username": test_user_data["username"],
            "password": test_user_data["password"]
        }
        user1_login = client.post("/auth/login", data=login_data)
        user1_token = user1_login.json()["access_token"]
        
        # Register user 2
        client.post("/auth/register", json=test_user_two)
        
        # User 1 gets their own info
        headers = {"Authorization": f"Bearer {user1_token}"}
        response = client.get("/auth/me", headers=headers)
        assert response.json()["username"] == test_user_data["username"]
        assert response.json()["id"] == user1_id
