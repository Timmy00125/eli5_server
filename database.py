"""
Database configuration and models for the ELI5 application.
Handles user authentication and history management.
"""

import os
from datetime import datetime
from logging import Logger
from typing import Any, Generator, List

from dotenv import load_dotenv
from sqlalchemy import (
    Column,
    DateTime,
    Engine,
    ForeignKey,
    Integer,
    String,
    Text,
    create_engine,
)
from sqlalchemy.orm import Mapped, declarative_base, relationship, sessionmaker
from sqlalchemy.orm.session import Session
from sqlalchemy.sql import func

load_dotenv()

# Database URL configuration
# For development: Use SQLite (file-based, no server needed)
# For production: Set DATABASE_URL environment variable to PostgreSQL URL
DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./eli5_dev.db")

# Create engine with appropriate settings for SQLite
if DATABASE_URL.startswith("sqlite"):
    # SQLite-specific configuration
    engine: Engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},  # Needed for SQLite with FastAPI
    )
else:
    # PostgreSQL or other database configuration
    engine = create_engine(DATABASE_URL)

# Create SessionLocal class
SessionLocal: sessionmaker[Session] = sessionmaker(
    autocommit=False, autoflush=False, bind=engine
)

# Create Base class
Base: Any = declarative_base()


class User(Base):
    """
    User model for authentication and profile management.
    Stores user credentials and basic information.
    """

    __tablename__: str = "users"

    id: Column[int] = Column(Integer, primary_key=True, index=True)
    email: Column[str] = Column(String, unique=True, index=True, nullable=False)
    username: Column[str] = Column(String, unique=True, index=True, nullable=False)
    hashed_password: Column[str] = Column(String, nullable=False)
    created_at: Column[datetime] = Column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Column[datetime] = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationship to history entries
    history_entries: Mapped[List["HistoryEntry"]] = relationship(
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

    __tablename__: str = "history_entries"

    id: Column[int] = Column(Integer, primary_key=True, index=True)
    user_id: Column[int] = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    concept: Column[str] = Column(String, nullable=False)
    explanation: Column[str] = Column(Text, nullable=False)
    created_at: Column[datetime] = Column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationship to user
    user: Mapped["User"] = relationship("User", back_populates="history_entries")


def get_db() -> Generator[Session, Any, None]:
    """
    Dependency to get database session.
    Ensures proper session management and cleanup.
    """
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables() -> None:
    """
    Create all database tables.
    Should be called when initializing the application.
    """
    import logging

    logger: Logger = logging.getLogger(__name__)
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
