# TicTacToe FastAPI Game REST API

A RESTful API for playing TicTacToe with user authentication, game management, and automatic win/draw detection.

## Features

- **User Authentication**: JWT-based authentication with registration and login
- **Game Management**: Create, retrieve, and delete games
- **Move Validation**: Automatic validation of moves and turn management
- **Win Detection**: Automatic detection of wins (rows, columns, diagonals) and draws
- **Move History**: Complete move history for all games
- **RESTful Design**: Clean, well-documented API endpoints
- **PostgreSQL Database**: Persistent storage with SQLAlchemy ORM
- **Swagger Documentation**: Interactive API documentation at `/docs`

## Architecture

```
TicTacToe/
├── app/
│   ├── api/           # API endpoints (auth, games)
│   ├── crud/          # Database operations
│   ├── engine/        # Database engine & session management
│   ├── model/         # SQLAlchemy models
│   ├── schema/        # Pydantic schemas (DTOs)
│   ├── services/      # Business logic (game rules, authentication)
│   ├── main.py        # FastAPI application
│   └── init_db.py     # Database initialization script
├── tests/             # Unit tests
├── docker-compose.yml # PostgreSQL & pgAdmin setup
├── run.py            # Application entry point
└── pyproject.toml    # Project dependencies
```

## Requirements

- Python 3.12+
- PostgreSQL (via Docker)
- uv (Python package manager)

## Setup & Installation

### 1. Start PostgreSQL Database

```bash
docker compose up -d
```

This starts:
- PostgreSQL on port `5432`
- pgAdmin on port `8080` (http://localhost:8080)

### 2. Install Dependencies

```bash
uv sync
```

### 3. Initialize Database

```bash
uv run python app/init_db.py
```

This creates:
- Database `tictactoe`
- Tables: `users`, `games`, `moves`

### 4. Start the API Server

```bash
uv run python run.py
```

The API will be available at:
- **API**: http://localhost:8000
- **Swagger Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## API Endpoints

### Authentication

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/auth/register` | Register a new user |
| POST | `/auth/login` | Login and receive JWT token |
| GET | `/auth/me` | Get current user info |

### Games

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/games` | Create a new game |
| GET | `/games` | Get all games with move histories |
| GET | `/games/{game_id}` | Get specific game details |
| GET | `/games/{game_id}/board` | Get visual board representation |
| PUT | `/games/{game_id}/move/{position}` | Make a move (position 1-9) |
| DELETE | `/games/{game_id}` | Delete a game |
| DELETE | `/games/completed/all` | Delete all completed games |
| GET | `/games/user/me` | Get current user's games |

## Game Flow Example

### 1. Register User

```bash
curl -X POST "http://localhost:8000/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "player1",
    "email": "player1@example.com",
    "password": "password123"
  }'
```

### 2. Login

```bash
curl -X POST "http://localhost:8000/auth/login" \
  -F "username=player1" \
  -F "password=password123"
```

Response:
```json
{
  "access_token": "eyJhbGc...",
  "token_type": "bearer"
}
```

### 3. Create Game

```bash
curl -X POST "http://localhost:8000/games" \
  -H "Authorization: Bearer <your_token>" \
  -H "Content-Type: application/json" \
  -d '{}'
```

### 4. Make Move

```bash
curl -X PUT "http://localhost:8000/games/{game_id}/move/5" \
  -H "Authorization: Bearer <your_token>"
```

## Board Positions

```
1 | 2 | 3
---------
4 | 5 | 6
---------
7 | 8 | 9
```

## Testing

### Run Tests

```bash
uv run pytest
```

### With Coverage

```bash
uv run pytest --cov=app --cov-report=html
```

## Database

### Connection Details

- **Host**: localhost
- **Port**: 5432
- **Database**: tictactoe
- **User**: admin
- **Password**: Kennwort1

### pgAdmin Access

- **URL**: http://localhost:8080
- **Email**: admin@pgadmin.com
- **Password**: Kennwort1

## Configuration

### Environment Variables

Copy `.env.example` to `.env` and adjust settings:

```bash
DATABASE_URL=postgresql://admin:Kennwort1@localhost:5432/tictactoe
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

**Important**: Change `SECRET_KEY` in production!

## Security Features

- Password hashing with bcrypt
- JWT token-based authentication
- Protected endpoints requiring authentication
- SQL injection prevention via ORM
- Input validation with Pydantic

## API Documentation

Interactive API documentation is automatically generated and available at:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Development

### Project Structure

- **models**: SQLAlchemy ORM models
- **schemas**: Pydantic validation schemas (DTOs)
- **crud**: Database operations (Create, Read, Update, Delete)
- **services**: Business logic (game rules, authentication)
- **api**: HTTP endpoint handlers

### Code Quality

- Type hints throughout codebase
- Comprehensive docstrings
- Modular architecture
- Clean separation of concerns

## License

MIT License - see LICENSE file for details

## Author

Leonardo Posch – HTL INSY 2025/26 (GitHub: @Poschi17)
