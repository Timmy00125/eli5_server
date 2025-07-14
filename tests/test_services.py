"""
Tests for services.py - Business logic and service layer operations.
Tests user management and history tracking services.
"""

import pytest
from unittest.mock import patch
from sqlalchemy.exc import IntegrityError

from services import UserService, HistoryService
from schemas import UserRegistration, SaveHistoryRequest
from database import User, HistoryEntry
from auth import verify_password


class TestUserService:
    """Test suite for UserService class."""

    def test_create_user_success(self, test_session):
        """
        Test successful user creation via UserService.

        Verifies:
        - User is created with correct data
        - Password is properly hashed
        - User is saved to database
        """
        user_data = UserRegistration(
            email="service@example.com",
            username="serviceuser",
            password="servicepassword123",
        )

        created_user = UserService.create_user(test_session, user_data)

        assert created_user is not None
        assert created_user.id is not None
        assert created_user.email == user_data.email
        assert created_user.username == user_data.username
        assert created_user.hashed_password != user_data.password  # Should be hashed
        assert verify_password(user_data.password, created_user.hashed_password)

        # Verify user is in database
        db_user = test_session.query(User).filter(User.email == user_data.email).first()
        assert db_user is not None
        assert db_user.id == created_user.id

    def test_create_user_duplicate_email(self, test_session, sample_user):
        """
        Test user creation with duplicate email.

        Verifies:
        - ValueError is raised for duplicate email
        - No user is created in database
        - Error message is descriptive
        """
        user_data = UserRegistration(
            email=sample_user.email,  # Duplicate email
            username="differentusername",
            password="password123",
        )

        with pytest.raises(ValueError) as exc_info:
            UserService.create_user(test_session, user_data)

        assert "Email already registered" in str(exc_info.value)

        # Verify no new user was created
        users_count = (
            test_session.query(User).filter(User.email == sample_user.email).count()
        )
        assert users_count == 1  # Only the original user

    def test_create_user_duplicate_username(self, test_session, sample_user):
        """
        Test user creation with duplicate username.

        Verifies:
        - ValueError is raised for duplicate username
        - No user is created in database
        - Error message is descriptive
        """
        user_data = UserRegistration(
            email="different@example.com",
            username=sample_user.username,  # Duplicate username
            password="password123",
        )

        with pytest.raises(ValueError) as exc_info:
            UserService.create_user(test_session, user_data)

        assert "Username already taken" in str(exc_info.value)

        # Verify no new user was created
        users_count = (
            test_session.query(User)
            .filter(User.username == sample_user.username)
            .count()
        )
        assert users_count == 1  # Only the original user

    def test_create_user_logging(self, test_session):
        """
        Test that user creation is properly logged.

        Verifies:
        - Log message is generated on successful creation
        - Log contains relevant user information
        """
        user_data = UserRegistration(
            email="logging@example.com", username="logginguser", password="password123"
        )

        with patch("services.logger") as mock_logger:
            UserService.create_user(test_session, user_data)

            mock_logger.info.assert_called_once()
            log_call = mock_logger.info.call_args[0][0]
            assert "New user created" in log_call
            assert user_data.email in log_call

    def test_get_user_by_id_existing_user(self, test_session, sample_user):
        """
        Test retrieving existing user by ID.

        Verifies:
        - Existing user is found and returned
        - All user data is correct
        """
        retrieved_user = UserService.get_user_by_id(test_session, sample_user.id)

        assert retrieved_user is not None
        assert retrieved_user.id == sample_user.id
        assert retrieved_user.email == sample_user.email
        assert retrieved_user.username == sample_user.username

    def test_get_user_by_id_nonexistent_user(self, test_session):
        """
        Test retrieving nonexistent user by ID.

        Verifies:
        - None is returned for nonexistent user
        - No exceptions are raised
        """
        retrieved_user = UserService.get_user_by_id(test_session, 99999)

        assert retrieved_user is None

    def test_create_user_password_validation(self, test_session):
        """
        Test that user creation validates password requirements.

        Verifies:
        - Password requirements are enforced by schema
        - Short passwords are rejected
        """
        # This test depends on Pydantic validation in UserRegistration schema
        with pytest.raises(ValueError):
            UserRegistration(
                email="test@example.com",
                username="testuser",
                password="123",  # Too short, should fail validation
            )

    def test_create_user_email_validation(self, test_session):
        """
        Test that user creation validates email format.

        Verifies:
        - Email format is validated by schema
        - Invalid emails are rejected
        """
        # This test depends on Pydantic validation in UserRegistration schema
        with pytest.raises(ValueError):
            UserRegistration(
                email="invalid-email",  # Invalid format
                username="testuser",
                password="password123",
            )

    def test_create_user_username_validation(self, test_session):
        """
        Test that user creation validates username requirements.

        Verifies:
        - Username length requirements are enforced
        - Short usernames are rejected
        """
        # This test depends on Pydantic validation in UserRegistration schema
        with pytest.raises(ValueError):
            UserRegistration(
                email="test@example.com",
                username="ab",  # Too short
                password="password123",
            )


class TestHistoryService:
    """Test suite for HistoryService class."""

    def test_save_history_entry_success(self, test_session, sample_user):
        """
        Test successful history entry creation.

        Verifies:
        - History entry is created with correct data
        - Entry is linked to correct user
        - Entry is saved to database
        """
        history_data = SaveHistoryRequest(
            concept="Algorithm",
            explanation="A step-by-step procedure for solving problems",
        )

        created_entry = HistoryService.save_history_entry(
            test_session, sample_user.id, history_data
        )

        assert created_entry is not None
        assert created_entry.id is not None
        assert created_entry.user_id == sample_user.id
        assert created_entry.concept == history_data.concept
        assert created_entry.explanation == history_data.explanation
        assert created_entry.created_at is not None

        # Verify entry is in database
        db_entry = (
            test_session.query(HistoryEntry)
            .filter(HistoryEntry.id == created_entry.id)
            .first()
        )
        assert db_entry is not None
        assert db_entry.concept == history_data.concept

    def test_save_history_entry_logging(self, test_session, sample_user):
        """
        Test that history entry creation is properly logged.

        Verifies:
        - Log message is generated on successful creation
        - Log contains relevant entry information
        """
        history_data = SaveHistoryRequest(
            concept="Variable", explanation="Storage location for data"
        )

        with patch("services.logger") as mock_logger:
            HistoryService.save_history_entry(
                test_session, sample_user.id, history_data
            )

            mock_logger.info.assert_called_once()
            log_call = mock_logger.info.call_args[0][0]
            assert "History entry saved" in log_call
            assert str(sample_user.id) in log_call
            assert history_data.concept in log_call

    def test_save_history_entry_invalid_user(self, test_session):
        """
        Test history entry creation with invalid user ID.

        Verifies:
        - Database constraint error is raised
        - No entry is created in database
        """
        history_data = SaveHistoryRequest(
            concept="Test", explanation="Test explanation"
        )

        with pytest.raises(IntegrityError):
            HistoryService.save_history_entry(
                test_session,
                99999,
                history_data,  # Invalid user_id
            )

    def test_get_user_history_default_pagination(self, test_session, sample_user):
        """
        Test retrieving user history with default pagination.

        Verifies:
        - History entries are returned in correct order (newest first)
        - Pagination defaults work correctly
        - Total count is accurate
        """
        # Create multiple history entries
        entries_data = [
            {"concept": "Algorithm", "explanation": "Step by step"},
            {"concept": "Variable", "explanation": "Data storage"},
            {"concept": "Function", "explanation": "Reusable code"},
        ]

        created_entries = []
        for entry_data in entries_data:
            history_request = SaveHistoryRequest(**entry_data)
            entry = HistoryService.save_history_entry(
                test_session, sample_user.id, history_request
            )
            created_entries.append(entry)

        # Get user history
        entries, total = HistoryService.get_user_history(test_session, sample_user.id)

        assert len(entries) >= 3
        assert total >= 3
        assert total == len(entries)  # Should be same with default pagination

        # Verify ordering (newest first)
        for i in range(len(entries) - 1):
            assert entries[i].created_at >= entries[i + 1].created_at

    def test_get_user_history_custom_pagination(self, test_session, sample_user):
        """
        Test retrieving user history with custom pagination.

        Verifies:
        - Limit parameter works correctly
        - Offset parameter works correctly
        - Total count is accurate regardless of pagination
        """
        # Create multiple history entries
        for i in range(5):
            history_request = SaveHistoryRequest(
                concept=f"Concept {i}", explanation=f"Explanation {i}"
            )
            HistoryService.save_history_entry(
                test_session, sample_user.id, history_request
            )

        # Test with limit
        entries, total = HistoryService.get_user_history(
            test_session, sample_user.id, limit=2
        )
        assert len(entries) == 2
        assert total >= 5  # Total should be full count

        # Test with offset
        entries_offset, total_offset = HistoryService.get_user_history(
            test_session, sample_user.id, limit=2, offset=2
        )
        assert len(entries_offset) == 2
        assert total_offset == total  # Total should be same

        # Verify different entries are returned
        first_page_ids = {entry.id for entry in entries}
        second_page_ids = {entry.id for entry in entries_offset}
        assert first_page_ids.isdisjoint(second_page_ids)

    def test_get_user_history_empty_result(self, test_session, sample_user):
        """
        Test retrieving history for user with no entries.

        Verifies:
        - Empty list is returned
        - Total count is zero
        - No exceptions are raised
        """
        # Ensure user has no history entries
        test_session.query(HistoryEntry).filter(
            HistoryEntry.user_id == sample_user.id
        ).delete()
        test_session.commit()

        entries, total = HistoryService.get_user_history(test_session, sample_user.id)

        assert entries == []
        assert total == 0

    def test_get_user_history_nonexistent_user(self, test_session):
        """
        Test retrieving history for nonexistent user.

        Verifies:
        - Empty list is returned for nonexistent user
        - Total count is zero
        - No exceptions are raised
        """
        entries, total = HistoryService.get_user_history(test_session, 99999)

        assert entries == []
        assert total == 0

    def test_get_history_entry_by_id_existing_entry(
        self, test_session, sample_history_entry
    ):
        """
        Test retrieving existing history entry by ID.

        Verifies:
        - Existing entry is found and returned
        - User ownership is verified
        - All entry data is correct
        """
        entry = HistoryService.get_history_entry_by_id(
            test_session, sample_history_entry.id, sample_history_entry.user_id
        )

        assert entry is not None
        assert entry.id == sample_history_entry.id
        assert entry.user_id == sample_history_entry.user_id
        assert entry.concept == sample_history_entry.concept

    def test_get_history_entry_by_id_wrong_user(
        self, test_session, sample_history_entry
    ):
        """
        Test retrieving history entry with wrong user ID.

        Verifies:
        - None is returned when user doesn't own entry
        - Security check works correctly
        """
        wrong_user_id = sample_history_entry.user_id + 1000

        entry = HistoryService.get_history_entry_by_id(
            test_session, sample_history_entry.id, wrong_user_id
        )

        assert entry is None

    def test_get_history_entry_by_id_nonexistent_entry(self, test_session, sample_user):
        """
        Test retrieving nonexistent history entry.

        Verifies:
        - None is returned for nonexistent entry
        - No exceptions are raised
        """
        entry = HistoryService.get_history_entry_by_id(
            test_session, 99999, sample_user.id
        )

        assert entry is None

    def test_delete_history_entry_success(self, test_session, sample_history_entry):
        """
        Test successful history entry deletion.

        Verifies:
        - Entry is deleted from database
        - True is returned on successful deletion
        - User ownership is verified before deletion
        """
        entry_id = sample_history_entry.id
        user_id = sample_history_entry.user_id

        result = HistoryService.delete_history_entry(test_session, entry_id, user_id)

        assert result is True

        # Verify entry is deleted
        deleted_entry = (
            test_session.query(HistoryEntry).filter(HistoryEntry.id == entry_id).first()
        )
        assert deleted_entry is None

    def test_delete_history_entry_wrong_user(self, test_session, sample_history_entry):
        """
        Test history entry deletion with wrong user ID.

        Verifies:
        - False is returned when user doesn't own entry
        - Entry is not deleted
        - Security check works correctly
        """
        entry_id = sample_history_entry.id
        wrong_user_id = sample_history_entry.user_id + 1000

        result = HistoryService.delete_history_entry(
            test_session, entry_id, wrong_user_id
        )

        assert result is False

        # Verify entry still exists
        existing_entry = (
            test_session.query(HistoryEntry).filter(HistoryEntry.id == entry_id).first()
        )
        assert existing_entry is not None

    def test_delete_history_entry_nonexistent_entry(self, test_session, sample_user):
        """
        Test deletion of nonexistent history entry.

        Verifies:
        - False is returned for nonexistent entry
        - No exceptions are raised
        """
        result = HistoryService.delete_history_entry(
            test_session, 99999, sample_user.id
        )

        assert result is False

    def test_delete_history_entry_logging(self, test_session, sample_history_entry):
        """
        Test that history entry deletion is properly logged.

        Verifies:
        - Log message is generated on successful deletion
        - Log contains relevant entry information
        """
        entry_id = sample_history_entry.id
        user_id = sample_history_entry.user_id

        with patch("services.logger") as mock_logger:
            HistoryService.delete_history_entry(test_session, entry_id, user_id)

            mock_logger.info.assert_called_once()
            log_call = mock_logger.info.call_args[0][0]
            assert "History entry deleted" in log_call
            assert str(entry_id) in log_call
            assert str(user_id) in log_call


class TestServiceIntegration:
    """Test suite for service layer integration scenarios."""

    def test_user_creation_and_history_flow(self, test_session):
        """
        Test complete flow from user creation to history management.

        Verifies:
        - User can be created
        - History entries can be added for user
        - History can be retrieved and managed
        """
        # Create user
        user_data = UserRegistration(
            email="integration@example.com",
            username="integrationuser",
            password="password123",
        )
        user = UserService.create_user(test_session, user_data)

        # Add history entries
        history_items = [
            {"concept": "Algorithm", "explanation": "Step by step"},
            {"concept": "Variable", "explanation": "Data storage"},
        ]

        created_entries = []
        for item in history_items:
            history_request = SaveHistoryRequest(**item)
            entry = HistoryService.save_history_entry(
                test_session, user.id, history_request
            )
            created_entries.append(entry)

        # Retrieve history
        entries, total = HistoryService.get_user_history(test_session, user.id)

        assert len(entries) == 2
        assert total == 2
        assert all(entry.user_id == user.id for entry in entries)

        # Test individual entry retrieval
        first_entry = HistoryService.get_history_entry_by_id(
            test_session, created_entries[0].id, user.id
        )
        assert first_entry is not None
        assert first_entry.concept in [item["concept"] for item in history_items]

    def test_multiple_users_isolation(self, test_session):
        """
        Test that different users' data is properly isolated.

        Verifies:
        - Users can't access each other's history
        - History operations respect user ownership
        """
        import uuid

        # Create two users with unique identifiers
        unique_id1 = str(uuid.uuid4())[:8]
        unique_id2 = str(uuid.uuid4())[:8]

        user1_data = UserRegistration(
            email=f"user1{unique_id1}@example.com",
            username=f"user1{unique_id1}",
            password="password1",
        )
        user2_data = UserRegistration(
            email=f"user2{unique_id2}@example.com",
            username=f"user2{unique_id2}",
            password="password2",
        )

        user1 = UserService.create_user(test_session, user1_data)
        user2 = UserService.create_user(test_session, user2_data)

        # Add history for each user
        history1 = SaveHistoryRequest(
            concept="User1 Concept", explanation="User1 explanation"
        )
        history2 = SaveHistoryRequest(
            concept="User2 Concept", explanation="User2 explanation"
        )

        entry1 = HistoryService.save_history_entry(test_session, user1.id, history1)
        entry2 = HistoryService.save_history_entry(test_session, user2.id, history2)

        # Verify isolation
        user1_entries, user1_total = HistoryService.get_user_history(
            test_session, user1.id
        )
        user2_entries, user2_total = HistoryService.get_user_history(
            test_session, user2.id
        )

        assert user1_total == 1
        assert user2_total == 1
        assert user1_entries[0].concept == "User1 Concept"
        assert user2_entries[0].concept == "User2 Concept"

        # Verify cross-user access protection
        user1_cannot_access = HistoryService.get_history_entry_by_id(
            test_session, entry2.id, user1.id
        )
        user2_cannot_access = HistoryService.get_history_entry_by_id(
            test_session, entry1.id, user2.id
        )

        assert user1_cannot_access is None
        assert user2_cannot_access is None

    def test_service_error_handling(self, test_session):
        """
        Test error handling in service layer.

        Verifies:
        - Services handle database errors gracefully
        - Appropriate exceptions are raised
        """
        # Test duplicate user creation error handling
        user_data = UserRegistration(
            email="duplicate@example.com",
            username="duplicateuser",
            password="password123",
        )

        # Create first user
        UserService.create_user(test_session, user_data)

        # Try to create duplicate user
        with pytest.raises(ValueError):
            UserService.create_user(test_session, user_data)

        # Test history creation with invalid user
        invalid_history = SaveHistoryRequest(concept="Test", explanation="Test")

        with pytest.raises(IntegrityError):
            HistoryService.save_history_entry(test_session, 99999, invalid_history)

    def test_service_transaction_behavior(self, test_session):
        """
        Test transaction behavior in service operations.

        Verifies:
        - Services properly commit transactions
        - Data is persisted correctly
        """
        user_data = UserRegistration(
            email="transaction@example.com",
            username="transactionuser",
            password="password123",
        )

        # Create user
        user = UserService.create_user(test_session, user_data)

        # Verify user is committed and can be found in new query
        found_user = test_session.query(User).filter(User.id == user.id).first()
        assert found_user is not None

        # Add history entry
        history_data = SaveHistoryRequest(
            concept="Transaction Test", explanation="Testing transactions"
        )
        entry = HistoryService.save_history_entry(test_session, user.id, history_data)

        # Verify entry is committed
        found_entry = (
            test_session.query(HistoryEntry).filter(HistoryEntry.id == entry.id).first()
        )
        assert found_entry is not None
