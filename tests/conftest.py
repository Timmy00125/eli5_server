"""
Pytest configuration file for ELI5 Server tests.
Defines fixtures, test settings, and common test utilities.
"""

import os
import tempfile
from unittest.mock import Mock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Set test environment variables before importing app modules
os.environ["DATABASE_URL"] = "sqlite:///./test_eli5.db"
os.environ["SECRET_KEY"] = "test-secret-key-for-testing-only"
os.environ["GEMINI_API_KEY"] = "test-api-key"
os.environ["GEMINI_MODEL"] = "gemini-pro"
os.environ["DEBUG"] = "True"

from database import Base, HistoryEntry, User, get_db
from main import app


@pytest.fixture(scope="session")
def test_db():
    """
    Create a test database for the entire test session.
    Uses SQLite in-memory database for fast testing.
    """

    db_fd: int
    db_path: str
    db_fd, db_path = tempfile.mkstemp()
    test_database_url: str = f"sqlite:///{db_path}"

    engine = create_engine(
        test_database_url,
        connect_args={"check_same_thread": False},
        # Enable foreign key constraints for SQLite
        poolclass=None,
    )

    # Enable foreign key constraints for SQLite
    from sqlalchemy import event

    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        if "sqlite" in str(engine.url):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

    Base.metadata.create_all(bind=engine)

    yield engine, db_path

    os.close(db_fd)
    os.unlink(db_path)


@pytest.fixture
def test_session(test_db) -> "sessionmaker":  # type: ignore[no-untyped-def, misc]
    """
    Create a database session for each test.
    Rolls back transactions after each test to ensure test isolation.
    """
    engine, _ = test_db  # type: ignore[misc]
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)  # type: ignore[arg-type]
    session = TestingSessionLocal()  # type: ignore[call-arg]
    yield session  # type: ignore[misc]
    session.close()  # type: ignore[misc]


@pytest.fixture
def client(test_session) -> TestClient:  # type: ignore[no-untyped-def, misc]
    """
    Create a test client with test database dependency override.
    """

    def override_get_db():  # type: ignore[misc]
        try:
            yield test_session  # type: ignore[misc]
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db  # type: ignore[misc]

    with TestClient(app) as test_client:
        yield test_client  # type: ignore[misc]

    app.dependency_overrides.clear()  # type: ignore[misc]


@pytest.fixture
def mock_gemini_client():  # type: ignore
    """
    Mock Gemini API client for testing API endpoints without external dependencies.
    """
    with patch("main.client") as mock_client:  # type: ignore[attr-defined]
        mock_response = Mock()
        mock_response.text = "This is a test explanation for testing purposes."
        mock_client.models.generate_content.return_value = mock_response
        yield mock_client


@pytest.fixture
def sample_user_data() -> dict[str, str]:
    """
    Sample user data for testing user creation and authentication.
    """
    import uuid

    unique_id = str(uuid.uuid4())[:8]
    return {
        "email": f"test{unique_id}@example.com",
        "username": f"testuser{unique_id}",
        "password": "testpassword123",
    }  # type: ignore[misc]


@pytest.fixture
def sample_user(test_session, sample_user_data) -> User:  # type: ignore[no-untyped-def, misc]
    """
    Create a sample user in the test database.
    """
    from auth import hash_password  # type: ignore

    user = User(
        email=sample_user_data["email"],
        username=sample_user_data["username"],
        hashed_password=hash_password(sample_user_data["password"]),  # type: ignore
    )  # type: ignore[misc]
    test_session.add(user)  # type: ignore[misc]
    test_session.commit()  # type: ignore[misc]
    test_session.refresh(user)  # type: ignore[misc]

    return user  # type: ignore[misc]


@pytest.fixture
def auth_headers(sample_user) -> dict[str, str]:  # type: ignore[no-untyped-def, misc]
    """
    Create authentication headers for testing protected endpoints.
    """
    from auth import create_access_token  # type: ignore

    token = create_access_token(data={"sub": sample_user.email})  # type: ignore[misc]
    return {"Authorization": f"Bearer {token}"}  # type: ignore[misc]


@pytest.fixture
def sample_history_entry_data() -> dict[str, str]:
    """
    Sample history entry data for testing history operations.
    """
    return {
        "concept": "Algorithm",
        "explanation": "An algorithm is like a recipe for solving problems step by step.",
    }  # type: ignore[misc]


@pytest.fixture
def sample_history_entry(test_session, sample_user, sample_history_entry_data):  # type: ignore[no-untyped-def, misc]
    """
    Create a sample history entry in the test database.
    """
    history_entry = HistoryEntry(
        user_id=sample_user.id,  # type: ignore
        concept=sample_history_entry_data["concept"],
        explanation=sample_history_entry_data["explanation"],
    )  # type: ignore[misc]
    test_session.add(history_entry)  # type: ignore[misc]
    test_session.commit()  # type: ignore[misc]
    test_session.refresh(history_entry)  # type: ignore[misc]

    return history_entry  # type: ignore[misc]


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
