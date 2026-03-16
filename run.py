"""
Run script for the TicTacToe API.
Sets up the Python path and starts the server.
"""
import sys
from pathlib import Path

# Add app directory to Python path
app_dir = Path(__file__).parent / "app"
sys.path.insert(0, str(app_dir))

from config import env_str, env_int, env_bool

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=env_str("API_HOST", "127.0.0.1"),
        port=env_int("API_PORT", 8000),
        reload=env_bool("DEBUG", True),
        log_level="debug" if env_bool("DEBUG", True) else "info"
    )
