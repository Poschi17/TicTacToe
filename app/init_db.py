"""
Database initialization script.
Run this to create the database and tables.
"""
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# Database connection parameters
DB_HOST = "localhost"
DB_PORT = "5432"
DB_USER = "admin"
DB_PASSWORD = "Kennwort1"
DB_NAME = "tictactoe"


def create_database():
    """Create the tictactoe database if it doesn't exist."""
    try:
        # Connect to PostgreSQL server (default postgres database)
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            database="postgres"
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # Check if database exists
        cursor.execute(
            "SELECT 1 FROM pg_catalog.pg_database WHERE datname = %s",
            (DB_NAME,)
        )
        exists = cursor.fetchone()
        
        if not exists:
            # Create database
            cursor.execute(f'CREATE DATABASE {DB_NAME}')
            print(f"Database '{DB_NAME}' created successfully!")
        else:
            print(f"Database '{DB_NAME}' already exists.")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"Error creating database: {e}")
        raise


def init_tables():
    """Initialize database tables using SQLAlchemy."""
    try:
        from engine import init_db
        init_db()
        print("Database tables created successfully!")
    except Exception as e:
        print(f"Error creating tables: {e}")
        raise


if __name__ == "__main__":
    print("Initializing TicTacToe Database...")
    print("=" * 50)
    
    # Create database
    print("\n1. Creating database...")
    create_database()
    
    # Create tables
    print("\n2. Creating tables...")
    init_tables()
    
    print("\n" + "=" * 50)
    print("Database initialization complete!")
    print(f"\nDatabase URL: postgresql://{DB_USER}:***@{DB_HOST}:{DB_PORT}/{DB_NAME}")
