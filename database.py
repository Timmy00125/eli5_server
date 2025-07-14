"""
Database configuration and models for the ELI5 application.
Handles user authentication and history management.
"""

import os
from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    Text,
    DateTime,
    ForeignKey,
)
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.sql import func
from dotenv import load_dotenv

load_dotenv()

# Database URL configuration
# For development: Use SQLite (file-based, no server needed)
# For production: Set DATABASE_URL environment variable to PostgreSQL URL
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./eli5_dev.db")

# Create engine with appropriate settings for SQLite
if DATABASE_URL.startswith("sqlite"):
    # SQLite-specific configuration
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},  # Needed for SQLite with FastAPI
    )
else:
    # PostgreSQL or other database configuration
    engine = create_engine(DATABASE_URL)

# Create SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create Base class
Base = declarative_base()


class User(Base):
    """
    User model for authentication and profile management.
    Stores user credentials and basic information.
    """

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationship to history entries
    history_entries = relationship(
        "HistoryEntry",
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class HistoryEntry(Base):
    """
    History model to store user's past concept explanations.
    Links to the User model to provide personalized history.
    """

    __tablename__ = "history_entries"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    concept = Column(String, nullable=False)
    explanation = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationship to user
    user = relationship("User", back_populates="history_entries")


def get_db():
    """
    Dependency to get database session.
    Ensures proper session management and cleanup.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables():
    """
    Create all database tables.
    Should be called when initializing the application.
    """
    import logging

    logger = logging.getLogger(__name__)
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully.")
    except Exception as e:
        logger.error(f"Failed to create database tables: {str(e)}")
        logger.warning(
            "Database may not be available. Please check your DATABASE_URL configuration."
        )
        # Don't re-raise the exception to allow the app to start without DB
        # raise
