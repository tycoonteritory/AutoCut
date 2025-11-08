"""
Database configuration and session management
"""
import logging
import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from pathlib import Path

logger = logging.getLogger(__name__)

# Database file location
DB_DIR = Path(__file__).parent.parent.parent / "data"
DB_DIR.mkdir(exist_ok=True)

# Ensure the data directory has proper permissions
try:
    os.chmod(DB_DIR, 0o755)
except Exception as e:
    logger.warning(f"Could not set permissions on data directory: {e}")

DATABASE_URL = f"sqlite:///{DB_DIR / 'autocut.db'}"

# Create engine
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}  # Needed for SQLite
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()


def get_db():
    """
    Get database session

    Yields:
        Database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database tables"""
    logger.info(f"Initializing database at {DATABASE_URL}")

    # Create the database file and tables
    Base.metadata.create_all(bind=engine)

    # Ensure the database file has proper permissions
    db_file = DB_DIR / 'autocut.db'
    if db_file.exists():
        try:
            os.chmod(db_file, 0o666)
            logger.info("Database file permissions set to 0o666")
        except Exception as e:
            logger.warning(f"Could not set permissions on database file: {e}")

    logger.info("Database initialized successfully")
