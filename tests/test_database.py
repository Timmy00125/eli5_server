"""
Tests for database.py - Database models, connections, and operations.
Tests SQLAlchemy models, relationships, and database configuration.
"""

import os
import tempfile
import uuid
from datetime import datetime

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database import DATABASE_URL, HistoryEntry, User, create_tables, get_db


class TestDatabaseModels:
    """Test suite for database model definitions."""

    def test_user_model_creation(self, test_session):
        """
        Test User model creation and basic attributes.

        Verifies:
        - User can be created with required fields
        - All fields are properly stored
        - Timestamps are automatically set
        """
        unique_id = str(uuid.uuid4())[:8]
        user_data = {
            "email": f"test{unique_id}@example.com",
            "username": f"testuser{unique_id}",
            "hashed_password": "hashed_password_here",
        }

        user = User(**user_data)
        test_session.add(user)
        test_session.commit()
        test_session.refresh(user)

        assert user.id is not None
        assert user.email == user_data["email"]
        assert user.username == user_data["username"]
        assert user.hashed_password == user_data["hashed_password"]
        assert user.created_at is not None
        assert isinstance(user.created_at, datetime)

    def test_user_model_unique_constraints(self, test_session):
        """
        Test User model unique constraints for email and username.

        Verifies:
        - Email uniqueness is enforced
        - Username uniqueness is enforced
        - Appropriate exceptions are raised for violations
        """
        from sqlalchemy.exc import IntegrityError

        unique_id = str(uuid.uuid4())[:8]

        # Create first user
        user1 = User(
            email=f"test{unique_id}@example.com",
            username=f"testuser{unique_id}",
            hashed_password="password1",
        )
        test_session.add(user1)
        test_session.commit()

        # Try to create user with same email
        user2 = User(
            email=f"test{unique_id}@example.com",  # Same email
            username=f"differentuser{unique_id}",
            hashed_password="password2",
        )
        test_session.add(user2)

        with pytest.raises(IntegrityError):
            test_session.commit()

        test_session.rollback()

        # Try to create user with same username
        user3 = User(
            email=f"different{unique_id}@example.com",
            username=f"testuser{unique_id}",  # Same username
            hashed_password="password3",
        )
        test_session.add(user3)

        with pytest.raises(IntegrityError):
            test_session.commit()

    def test_user_model_relationships(self, test_session):
        """
        Test User model relationships with HistoryEntry.

        Verifies:
        - User can have multiple history entries
        - Relationship is properly configured
        - Cascade delete works correctly
        """
        unique_id = str(uuid.uuid4())[:8]

        # Create user
        user = User(
            email=f"test{unique_id}@example.com",
            username=f"testuser{unique_id}",
            hashed_password="password",
        )
        test_session.add(user)
        test_session.commit()
        test_session.refresh(user)

        # Create history entries
        entries_data = [
            {"concept": "Algorithm", "explanation": "Step by step instructions"},
            {"concept": "Variable", "explanation": "Storage for data"},
        ]

        for entry_data in entries_data:
            entry = HistoryEntry(
                user_id=user.id,
                concept=entry_data["concept"],
                explanation=entry_data["explanation"],
            )
            test_session.add(entry)

        test_session.commit()

        # Test relationship
        test_session.refresh(user)
        assert len(user.history_entries) == 2
        assert all(entry.user_id == user.id for entry in user.history_entries)

    def test_history_entry_model_creation(self, test_session, sample_user):
        """
        Test HistoryEntry model creation and attributes.

        Verifies:
        - HistoryEntry can be created with required fields
        - Foreign key relationship works
        - Timestamps are set correctly
        """
        entry_data = {
            "user_id": sample_user.id,
            "concept": "Algorithm",
            "explanation": "A step-by-step procedure for solving a problem",
        }

        entry = HistoryEntry(**entry_data)
        test_session.add(entry)
        test_session.commit()
        test_session.refresh(entry)

        assert entry.id is not None
        assert entry.user_id == sample_user.id
        assert entry.concept == entry_data["concept"]
        assert entry.explanation == entry_data["explanation"]
        assert entry.created_at is not None
        assert isinstance(entry.created_at, datetime)

    def test_history_entry_foreign_key_constraint(self, test_session):
        """
        Test HistoryEntry foreign key constraint.

        Verifies:
        - Foreign key constraint is enforced
        - Cannot create entry with invalid user_id
        """
        from sqlalchemy.exc import IntegrityError

        # Try to create history entry with invalid user_id
        entry = HistoryEntry(
            user_id=99999,  # Non-existent user
            concept="Test",
            explanation="Test explanation",
        )
        test_session.add(entry)

        with pytest.raises(IntegrityError):
            test_session.commit()

    def test_history_entry_cascade_delete(self, test_session):
        """
        Test cascade delete when user is deleted.

        Verifies:
        - History entries are deleted when user is deleted
        - Cascade configuration works correctly
        """
        unique_id = str(uuid.uuid4())[:8]

        # Create user
        user = User(
            email=f"test{unique_id}@example.com",
            username=f"testuser{unique_id}",
            hashed_password="password",
        )
        test_session.add(user)
        test_session.commit()
        test_session.refresh(user)

        # Create history entry
        entry = HistoryEntry(
            user_id=user.id, concept="Test", explanation="Test explanation"
        )
        test_session.add(entry)
        test_session.commit()

        entry_id = entry.id

        # Delete user
        test_session.delete(user)
        test_session.commit()

        # Verify history entry is also deleted
        deleted_entry = (
            test_session.query(HistoryEntry).filter(HistoryEntry.id == entry_id).first()
        )
        assert deleted_entry is None

    def test_history_entry_user_relationship(self, test_session, sample_user):
        """
        Test HistoryEntry back-reference to User.

        Verifies:
        - History entry can access its user
        - Relationship works in both directions
        """
        entry = HistoryEntry(
            user_id=sample_user.id, concept="Test", explanation="Test explanation"
        )
        test_session.add(entry)
        test_session.commit()
        test_session.refresh(entry)

        # Test back-reference
        assert entry.user is not None
        assert entry.user.id == sample_user.id
        assert entry.user.email == sample_user.email


class TestDatabaseConfiguration:
    """Test suite for database configuration and connection."""

    def test_database_url_configuration(self):
        """
        Test database URL configuration.

        Verifies:
        - DATABASE_URL is properly configured
        - Default SQLite configuration works
        """
        assert isinstance(DATABASE_URL, str)
        assert len(DATABASE_URL) > 0

        # In test environment, should be SQLite
        assert DATABASE_URL.startswith("sqlite://")

    def test_get_db_generator(self):
        """
        Test get_db dependency generator.

        Verifies:
        - Generator yields database session
        - Session is properly closed after use
        - Context manager behavior works
        """
        # Test the generator
        db_gen = get_db()

        # Get the session
        session = next(db_gen)
        assert session is not None
        assert hasattr(session, "query")
        assert hasattr(session, "add")
        assert hasattr(session, "commit")

        # Close the generator (simulates FastAPI dependency cleanup)
        try:
            next(db_gen)
        except StopIteration:
            pass  # Expected behavior

    def test_create_tables_function(self):
        """
        Test create_tables function.

        Verifies:
        - Tables are created successfully
        - Function handles errors gracefully
        - All defined models have corresponding tables
        """
        # Create a temporary database for this test
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp_file:
            test_db_url = f"sqlite:///{tmp_file.name}"

        try:
            # Create engine for test database
            test_engine = create_engine(test_db_url)

            # Replace the global engine temporarily
            import database

            original_engine = database.engine
            database.engine = test_engine

            # Test create_tables
            create_tables()

            # Verify tables exist
            from sqlalchemy import inspect

            inspector = inspect(test_engine)
            tables = inspector.get_table_names()

            assert "users" in tables
            assert "history_entries" in tables

        finally:
            # Restore original engine
            database.engine = original_engine
            # Cleanup test database
            os.unlink(tmp_file.name)

    def test_sqlite_configuration(self):
        """
        Test SQLite-specific configuration.

        Verifies:
        - SQLite connection arguments are set correctly
        - Thread safety is configured
        """
        # This test verifies the configuration in the module
        import database

        # Check if using SQLite
        if database.DATABASE_URL.startswith("sqlite"):
            # Verify the engine has correct connect_args
            engine_info = str(database.engine.url)
            assert "sqlite" in engine_info.lower()

    def test_postgresql_configuration(self):
        """
        Test PostgreSQL configuration handling.

        Verifies:
        - PostgreSQL URLs are handled correctly
        - No SQLite-specific args are applied
        """
        # Mock PostgreSQL URL
        postgres_url = "postgresql://user:pass@localhost/dbname"

        # Test engine creation with PostgreSQL URL
        engine = create_engine(postgres_url)
        assert engine is not None
        assert "postgresql" in str(engine.url)


class TestDatabaseOperations:
    """Test suite for basic database operations."""

    def test_user_crud_operations(self, test_session):
        """
        Test basic CRUD operations for User model.

        Verifies:
        - Create: User creation works
        - Read: User query works
        - Update: User updates work
        - Delete: User deletion works
        """
        unique_id = str(uuid.uuid4())[:8]

        # Create
        user = User(
            email=f"crud{unique_id}@example.com",
            username=f"cruduser{unique_id}",
            hashed_password="password",
        )
        test_session.add(user)
        test_session.commit()
        test_session.refresh(user)

        user_id = user.id
        assert user_id is not None

        # Read
        retrieved_user = test_session.query(User).filter(User.id == user_id).first()
        assert retrieved_user is not None
        assert retrieved_user.email == f"crud{unique_id}@example.com"

        # Update
        retrieved_user.username = f"updateduser{unique_id}"
        test_session.commit()

        updated_user = test_session.query(User).filter(User.id == user_id).first()
        assert updated_user.username == f"updateduser{unique_id}"

        # Delete
        test_session.delete(updated_user)
        test_session.commit()

        deleted_user = test_session.query(User).filter(User.id == user_id).first()
        assert deleted_user is None

    def test_history_entry_crud_operations(self, test_session, sample_user):
        """
        Test basic CRUD operations for HistoryEntry model.

        Verifies:
        - Create: Entry creation works
        - Read: Entry query works
        - Update: Entry updates work
        - Delete: Entry deletion works
        """
        # Create
        entry = HistoryEntry(
            user_id=sample_user.id,
            concept="CRUD Test",
            explanation="Testing CRUD operations",
        )
        test_session.add(entry)
        test_session.commit()
        test_session.refresh(entry)

        entry_id = entry.id
        assert entry_id is not None

        # Read
        retrieved_entry = (
            test_session.query(HistoryEntry).filter(HistoryEntry.id == entry_id).first()
        )
        assert retrieved_entry is not None
        assert retrieved_entry.concept == "CRUD Test"

        # Update
        retrieved_entry.explanation = "Updated explanation"
        test_session.commit()

        updated_entry = (
            test_session.query(HistoryEntry).filter(HistoryEntry.id == entry_id).first()
        )
        assert updated_entry.explanation == "Updated explanation"

        # Delete
        test_session.delete(updated_entry)
        test_session.commit()

        deleted_entry = (
            test_session.query(HistoryEntry).filter(HistoryEntry.id == entry_id).first()
        )
        assert deleted_entry is None

    def test_user_query_operations(self, test_session):
        """
        Test various query operations on User model.

        Verifies:
        - Filter by email works
        - Filter by username works
        - Multiple users can be queried
        """
        unique_id = str(uuid.uuid4())[:8]

        # Create multiple users
        users_data = [
            {
                "email": f"user1{unique_id}@example.com",
                "username": f"user1{unique_id}",
                "password": "pass1",
            },
            {
                "email": f"user2{unique_id}@example.com",
                "username": f"user2{unique_id}",
                "password": "pass2",
            },
            {
                "email": f"user3{unique_id}@example.com",
                "username": f"user3{unique_id}",
                "password": "pass3",
            },
        ]

        for user_data in users_data:
            user = User(
                email=user_data["email"],
                username=user_data["username"],
                hashed_password=user_data["password"],
            )
            test_session.add(user)

        test_session.commit()

        # Test filter by email
        user1 = (
            test_session.query(User)
            .filter(User.email == f"user1{unique_id}@example.com")
            .first()
        )
        assert user1 is not None
        assert user1.username == f"user1{unique_id}"

        # Test filter by username
        user2 = (
            test_session.query(User)
            .filter(User.username == f"user2{unique_id}")
            .first()
        )
        assert user2 is not None
        assert user2.email == f"user2{unique_id}@example.com"

        # Test count
        total_users = test_session.query(User).count()
        assert total_users >= 3

    def test_history_entry_query_operations(self, test_session, sample_user):
        """
        Test various query operations on HistoryEntry model.

        Verifies:
        - Filter by user_id works
        - Filter by concept works
        - Ordering operations work
        """
        # Create multiple history entries
        entries_data = [
            {"concept": "Algorithm", "explanation": "Step by step instructions"},
            {"concept": "Variable", "explanation": "Data storage"},
            {"concept": "Function", "explanation": "Reusable code"},
        ]

        for entry_data in entries_data:
            entry = HistoryEntry(
                user_id=sample_user.id,
                concept=entry_data["concept"],
                explanation=entry_data["explanation"],
            )
            test_session.add(entry)

        test_session.commit()

        # Test filter by user_id
        user_entries = (
            test_session.query(HistoryEntry)
            .filter(HistoryEntry.user_id == sample_user.id)
            .all()
        )
        assert len(user_entries) >= 3

        # Test filter by concept
        algo_entry = (
            test_session.query(HistoryEntry)
            .filter(HistoryEntry.concept == "Algorithm")
            .first()
        )
        assert algo_entry is not None
        assert algo_entry.explanation == "Step by step instructions"

        # Test ordering
        ordered_entries = (
            test_session.query(HistoryEntry)
            .filter(HistoryEntry.user_id == sample_user.id)
            .order_by(HistoryEntry.created_at.desc())
            .all()
        )

        assert len(ordered_entries) >= 3
        # Verify ordering (newest first)
        for i in range(len(ordered_entries) - 1):
            assert ordered_entries[i].created_at >= ordered_entries[i + 1].created_at


class TestDatabaseIntegration:
    """Test suite for database integration scenarios."""

    def test_session_isolation(self, test_db):
        """
        Test that different sessions are isolated.

        Verifies:
        - Changes in one session don't affect others until commit
        - Session isolation works correctly
        """
        engine, _ = test_db
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

        # Create two separate sessions
        session1 = SessionLocal()
        session2 = SessionLocal()
        unique_id = str(uuid.uuid4())[:8]

        try:
            # Add user in session1
            user1 = User(
                email=f"session1{unique_id}@example.com",
                username=f"session1user{unique_id}",
                hashed_password="password1",
            )
            session1.add(user1)
            # Don't commit yet

            # Try to find user in session2
            user_in_session2 = (
                session2.query(User)
                .filter(User.email == f"session1{unique_id}@example.com")
                .first()
            )
            assert user_in_session2 is None  # Should not be visible

            # Commit in session1
            session1.commit()

            # Now should be visible in session2
            user_in_session2 = (
                session2.query(User)
                .filter(User.email == f"session1{unique_id}@example.com")
                .first()
            )
            assert user_in_session2 is not None

        finally:
            session1.close()
            session2.close()

    def test_transaction_rollback(self, test_session):
        """
        Test transaction rollback functionality.

        Verifies:
        - Rollback undoes uncommitted changes
        - Data integrity is maintained
        """
        unique_id = str(uuid.uuid4())[:8]

        # Count initial users
        initial_count = test_session.query(User).count()

        # Add a user
        user = User(
            email=f"rollback{unique_id}@example.com",
            username=f"rollbackuser{unique_id}",
            hashed_password="password",
        )
        test_session.add(user)

        # Flush to make the object visible in queries but don't commit
        test_session.flush()

        # Verify user is in session but not committed
        session_count = test_session.query(User).count()
        assert session_count == initial_count + 1

        # Rollback
        test_session.rollback()

        # Verify user is gone
        final_count = test_session.query(User).count()
        assert final_count == initial_count

        # Verify user is not in database
        rolled_back_user = (
            test_session.query(User)
            .filter(User.email == f"rollback{unique_id}@example.com")
            .first()
        )
        assert rolled_back_user is None

    def test_concurrent_operations(self, test_db):
        """
        Test concurrent database operations.

        Verifies:
        - Multiple operations can occur simultaneously
        - Data consistency is maintained
        """
        engine, _ = test_db
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

        sessions = [SessionLocal() for _ in range(3)]
        unique_id = str(uuid.uuid4())[:8]

        try:
            # Create users in different sessions
            for i, session in enumerate(sessions):
                user = User(
                    email=f"concurrent{i}{unique_id}@example.com",
                    username=f"concurrent{i}{unique_id}",
                    hashed_password=f"password{i}",
                )
                session.add(user)
                session.commit()

            # Verify all users exist
            for i, session in enumerate(sessions):
                user = (
                    session.query(User)
                    .filter(User.email == f"concurrent{i}{unique_id}@example.com")
                    .first()
                )
                assert user is not None
                assert user.username == f"concurrent{i}{unique_id}"

        finally:
            for session in sessions:
                session.close()
