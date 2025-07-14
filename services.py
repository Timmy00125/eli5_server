"""
Service layer for user and history operations.
Contains business logic for user management and history tracking.
"""

from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc
from database import User, HistoryEntry
from auth import hash_password, get_user_by_email, get_user_by_username
from schemas import UserRegistration, SaveHistoryRequest
import logging

logger = logging.getLogger(__name__)


class UserService:
    """Service class for user-related operations."""

    @staticmethod
    def create_user(db: Session, user_data: UserRegistration) -> User:
        """
        Create a new user account.

        Args:
            db: Database session
            user_data: User registration data

        Returns:
            Created user object

        Raises:
            ValueError: If email or username already exists
        """
        # Check if email already exists
        existing_user = get_user_by_email(db, user_data.email)
        if existing_user:
            raise ValueError("Email already registered")

        # Check if username already exists
        existing_username = get_user_by_username(db, user_data.username)
        if existing_username:
            raise ValueError("Username already taken")

        # Create new user
        hashed_password = hash_password(user_data.password)
        db_user = User(
            email=user_data.email,
            username=user_data.username,
            hashed_password=hashed_password,
        )

        db.add(db_user)
        db.commit()
        db.refresh(db_user)

        logger.info(f"New user created: {user_data.email}")
        return db_user

    @staticmethod
    def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
        """
        Get user by ID.

        Args:
            db: Database session
            user_id: User ID

        Returns:
            User object if found, None otherwise
        """
        return db.query(User).filter(User.id == user_id).first()


class HistoryService:
    """Service class for history-related operations."""

    @staticmethod
    def save_history_entry(
        db: Session, user_id: int, history_data: SaveHistoryRequest
    ) -> HistoryEntry:
        """
        Save a new history entry for the user.

        Args:
            db: Database session
            user_id: User ID
            history_data: History entry data

        Returns:
            Created history entry
        """
        db_entry = HistoryEntry(
            user_id=user_id,
            concept=history_data.concept,
            explanation=history_data.explanation,
        )

        db.add(db_entry)
        db.commit()
        db.refresh(db_entry)

        logger.info(f"History entry saved for user {user_id}: {history_data.concept}")
        return db_entry

    @staticmethod
    def get_user_history(
        db: Session, user_id: int, limit: int = 50, offset: int = 0
    ) -> tuple[List[HistoryEntry], int]:
        """
        Get user's history entries with pagination.

        Args:
            db: Database session
            user_id: User ID
            limit: Maximum number of entries to return
            offset: Number of entries to skip

        Returns:
            Tuple of (history entries list, total count)
        """
        query = db.query(HistoryEntry).filter(HistoryEntry.user_id == user_id)

        # Get total count
        total = query.count()

        # Get paginated results, ordered by creation date (newest first)
        entries = (
            query.order_by(desc(HistoryEntry.created_at))
            .offset(offset)
            .limit(limit)
            .all()
        )

        return entries, total

    @staticmethod
    def get_history_entry_by_id(
        db: Session, entry_id: int, user_id: int
    ) -> Optional[HistoryEntry]:
        """
        Get a specific history entry for the user.

        Args:
            db: Database session
            entry_id: History entry ID
            user_id: User ID (for security check)

        Returns:
            History entry if found and belongs to user, None otherwise
        """
        return (
            db.query(HistoryEntry)
            .filter(HistoryEntry.id == entry_id, HistoryEntry.user_id == user_id)
            .first()
        )

    @staticmethod
    def delete_history_entry(db: Session, entry_id: int, user_id: int) -> bool:
        """
        Delete a history entry for the user.

        Args:
            db: Database session
            entry_id: History entry ID
            user_id: User ID (for security check)

        Returns:
            True if deleted successfully, False if not found
        """
        entry = HistoryService.get_history_entry_by_id(db, entry_id, user_id)
        if not entry:
            return False

        db.delete(entry)
        db.commit()

        logger.info(f"History entry deleted: {entry_id} for user {user_id}")
        return True
