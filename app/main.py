"""
FastAPI TicTacToe Game REST API
Main application module with API configuration and routing.
"""
from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from contextlib import asynccontextmanager
import textwrap

from engine import init_db
from api import auth, games


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events.
    Initializes the database on startup.
    """
    # Startup: Initialize database
    print("Starting TicTacToe API...")
    print("Initializing database...")
    init_db()
    print("Database initialized successfully!")
    
    yield
    
    # Shutdown
    print("Shutting down TicTacToe API...")


# Create FastAPI application
app = FastAPI(
    title="TicTacToe Game API",
    description=textwrap.dedent("""
    ## FastAPI TicTacToe Game REST API

    A RESTful API for playing TicTacToe with user authentication and game management.

    ### Features

    * **User Authentication**: JWT-based authentication with user registration and login
    * **Game Management**: Create, retrieve, and delete games
    * **Move Execution**: Make moves with automatic win/draw detection
    * **Game History**: View complete move histories for all games
    * **Game Logic**: Automatic validation of moves and game state

    ### Authentication

    1. Register a new user at `/auth/register`
    2. Login at `/auth/login` to receive a JWT token
    3. Use the token in the Authorization header: `Bearer <token>`
    4. All game endpoints require authentication

    ### Game Flow

    1. Create a new game with `POST /games`
    2. Make moves with `PUT /games/{game_id}/move/{position}`
    3. View game state and history with `GET /games/{game_id}`
    4. Delete completed games with `DELETE /games/{game_id}`

    ### Board Positions

    ```text
    1 | 2 | 3
    ---------
    4 | 5 | 6
    ---------
    7 | 8 | 9
    ```
    """),
    
    version="1.0.0",
    license_info={
        "name": "MIT License",
    },
    lifespan=lifespan
    
)

# Include routers
app.include_router(auth.router)
app.include_router(games.router)


@app.get("/", include_in_schema=False)
async def root():
    """Redirect root to API documentation."""
    return RedirectResponse(url="/docs", status_code=status.HTTP_307_TEMPORARY_REDIRECT)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
