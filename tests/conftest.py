"""
Pytest configuration file for ELI5 Server tests.
Defines fixtures, test settings, and common test utilities.
"""

import os
import tempfile
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import Mock, patch

# Set test environment variables before importing app modules
os.environ["DATABASE_URL"] = "sqlite:///./test_eli5.db"
os.environ["SECRET_KEY"] = "test-secret-key-for-testing-only"
os.environ["GEMINI_API_KEY"] = "test-api-key"
os.environ["GEMINI_MODEL"] = "gemini-pro"
os.environ["DEBUG"] = "True"

from database import Base, get_db, User, HistoryEntry
from main import app


@pytest.fixture(scope="session")
def test_db():
    """
    Create a test database for the entire test session.
    Uses SQLite in-memory database for fast testing.
    """
    # Create a temporary database file
    db_fd, db_path = tempfile.mkstemp()
    test_database_url = f"sqlite:///{db_path}"

    # Create test engine
    engine = create_engine(test_database_url, connect_args={"check_same_thread": False})

    # Create all tables
    Base.metadata.create_all(bind=engine)

    yield engine, db_path

    # Cleanup
    os.close(db_fd)
    os.unlink(db_path)


@pytest.fixture
def test_session(test_db):
    """
    Create a database session for each test.
    Rolls back transactions after each test to ensure test isolation.
    """
    engine, _ = test_db
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    session = TestingSessionLocal()

    yield session

    session.close()


@pytest.fixture
def client(test_session):
    """
    Create a test client with test database dependency override.
    """

    def override_get_db():
        try:
            yield test_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture
def mock_gemini_client():
    """
    Mock Gemini API client for testing API endpoints without external dependencies.
    """
    with patch("main.client") as mock_client:
        mock_response = Mock()
        mock_response.text = "This is a test explanation for testing purposes."
        mock_client.models.generate_content.return_value = mock_response
        yield mock_client


@pytest.fixture
def sample_user_data():
    """
    Sample user data for testing user creation and authentication.
    """
    return {
        "email": "test@example.com",
        "username": "testuser",
        "password": "testpassword123",
    }


@pytest.fixture
def sample_user(test_session, sample_user_data):
    """
    Create a sample user in the test database.
    """
    from auth import hash_password

    user = User(
        email=sample_user_data["email"],
        username=sample_user_data["username"],
        hashed_password=hash_password(sample_user_data["password"]),
    )
    test_session.add(user)
    test_session.commit()
    test_session.refresh(user)

    return user


@pytest.fixture
def auth_headers(sample_user):
    """
    Create authentication headers for testing protected endpoints.
    """
    from auth import create_access_token

    token = create_access_token(data={"sub": sample_user.email})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def sample_history_entry_data():
    """
    Sample history entry data for testing history operations.
    """
    return {
        "concept": "Algorithm",
        "explanation": "An algorithm is like a recipe for solving problems step by step.",
    }


@pytest.fixture
def sample_history_entry(test_session, sample_user, sample_history_entry_data):
    """
    Create a sample history entry in the test database.
    """
    history_entry = HistoryEntry(
        user_id=sample_user.id,
        concept=sample_history_entry_data["concept"],
        explanation=sample_history_entry_data["explanation"],
    )
    test_session.add(history_entry)
    test_session.commit()
    test_session.refresh(history_entry)

    return history_entry


# Test configuration
pytest_plugins = ["pytest_asyncio"]


# Configure asyncio for testing
@pytest.fixture(scope="session")
def event_loop():
    """
    Create an event loop for async test functions.
    """
    import asyncio

    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()
