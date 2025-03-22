"""Database connection helper for PostgreSQL."""
import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get database credentials from environment variables
DB_NAME = os.getenv("DB_NAME", "salesiq")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")

# Create database URL
DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"


def get_engine():
    """Create and return a SQLAlchemy engine using environment variables."""
    return create_engine(DATABASE_URL)


def get_session():
    """Create and return a new SQLAlchemy session."""
    engine = get_engine()
    Session = sessionmaker(bind=engine)
    return Session()


Base = declarative_base()


def execute_query(query, params=None, fetch=True):
    """
    Execute a raw SQL query and return results.
    
    Args:
        query (str): SQL query to execute
        params (dict, optional): Parameters for the query
        fetch (bool, optional): Whether to fetch results
        
    Returns:
        list: Query results if fetch is True, otherwise None
    """
    engine = get_engine()
    with engine.connect() as connection:
        if params:
            result = connection.execute(query, params)
        else:
            result = connection.execute(query)
            
        if fetch:
            return result.fetchall()
        return None


def test_connection():
    """Test the database connection and return status."""
    try:
        engine = get_engine()
        with engine.connect() as connection:
            result = connection.execute("SELECT 1")
            return True
    except Exception as e:
        print(f"Database connection error: {e}")
        return False 