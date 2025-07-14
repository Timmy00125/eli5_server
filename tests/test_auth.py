"""
Tests for auth.py - Authentication and authorization functionality.
Tests password hashing, JWT tokens, user verification, and security functions.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
from fastapi import HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials
from jose import jwt

from auth import (
    hash_password,
    verify_password,
    create_access_token,
    verify_token,
    get_user_by_email,
    get_user_by_username,
    authenticate_user,
    get_current_user,
    SECRET_KEY,
    ALGORITHM,
    ACCESS_TOKEN_EXPIRE_MINUTES,
)


class TestPasswordHashing:
    """Test suite for password hashing functionality."""

    def test_hash_password_creates_valid_hash(self):
        """
        Test that password hashing creates a valid bcrypt hash.

        Verifies:
        - Hash is generated for valid password
        - Hash is different from original password
        - Hash format is correct (bcrypt)
        """
        password = "testpassword123"
        hashed = hash_password(password)

        assert isinstance(hashed, str)
        assert hashed != password
        assert len(hashed) > 50  # bcrypt hashes are typically 60 characters
        assert hashed.startswith("$2b$")  # bcrypt format

    def test_hash_password_different_hashes_for_same_password(self):
        """
        Test that same password generates different hashes (salt).

        Verifies:
        - Same password produces different hashes due to salt
        - Both hashes are valid for the same password
        """
        password = "testpassword123"
        hash1 = hash_password(password)
        hash2 = hash_password(password)

        assert hash1 != hash2
        assert verify_password(password, hash1)
        assert verify_password(password, hash2)

    def test_verify_password_correct_password(self):
        """
        Test password verification with correct password.

        Verifies:
        - Correct password returns True
        - Case sensitivity is maintained
        """
        password = "testpassword123"
        hashed = hash_password(password)

        assert verify_password(password, hashed) is True

    def test_verify_password_incorrect_password(self):
        """
        Test password verification with incorrect password.

        Verifies:
        - Incorrect password returns False
        - Similar passwords are rejected
        """
        password = "testpassword123"
        wrong_password = "wrongpassword123"
        hashed = hash_password(password)

        assert verify_password(wrong_password, hashed) is False

    def test_verify_password_case_sensitive(self):
        """
        Test that password verification is case sensitive.

        Verifies:
        - Case differences are detected
        - Passwords with different cases are rejected
        """
        password = "TestPassword123"
        wrong_case = "testpassword123"
        hashed = hash_password(password)

        assert verify_password(wrong_case, hashed) is False

    def test_verify_password_empty_strings(self):
        """
        Test password verification with empty strings.

        Verifies:
        - Empty password against hash returns False
        - Function handles edge cases gracefully
        """
        password = "testpassword123"
        hashed = hash_password(password)

        assert verify_password("", hashed) is False


class TestJWTTokens:
    """Test suite for JWT token functionality."""

    def test_create_access_token_default_expiration(self):
        """
        Test JWT token creation with default expiration.

        Verifies:
        - Token is created successfully
        - Token format is valid JWT
        - Default expiration time is applied
        """
        data = {"sub": "test@example.com"}
        token = create_access_token(data)

        assert isinstance(token, str)
        assert len(token) > 0

        # Decode token to verify structure
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        assert payload["sub"] == "test@example.com"
        assert "exp" in payload

    def test_create_access_token_custom_expiration(self):
        """
        Test JWT token creation with custom expiration.

        Verifies:
        - Custom expiration time is applied
        - Token contains correct expiration timestamp
        """
        data = {"sub": "test@example.com"}
        custom_delta = timedelta(hours=1)
        token = create_access_token(data, expires_delta=custom_delta)

        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        # Check expiration is approximately 1 hour from now
        exp_time = datetime.fromtimestamp(payload["exp"])
        expected_time = datetime.utcnow() + custom_delta

        # Allow 10 second tolerance for test execution time
        time_diff = abs((exp_time - expected_time).total_seconds())
        assert time_diff < 10

    def test_create_access_token_with_additional_data(self):
        """
        Test JWT token creation with additional data fields.

        Verifies:
        - Additional data is preserved in token
        - All fields are accessible after decoding
        """
        data = {"sub": "test@example.com", "user_id": 123, "role": "user"}
        token = create_access_token(data)

        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        assert payload["sub"] == "test@example.com"
        assert payload["user_id"] == 123
        assert payload["role"] == "user"

    def test_verify_token_valid_token(self):
        """
        Test token verification with valid token.

        Verifies:
        - Valid token returns email
        - Email matches original data
        """
        email = "test@example.com"
        token = create_access_token({"sub": email})

        verified_email = verify_token(token)
        assert verified_email == email

    def test_verify_token_invalid_token(self):
        """
        Test token verification with invalid token.

        Verifies:
        - Invalid token returns None
        - Malformed tokens are rejected
        """
        invalid_token = "invalid.token.here"

        verified_email = verify_token(invalid_token)
        assert verified_email is None

    def test_verify_token_expired_token(self):
        """
        Test token verification with expired token.

        Verifies:
        - Expired token returns None
        - Expiration is properly enforced
        """
        # Create token that expired 1 minute ago
        expired_delta = timedelta(minutes=-1)
        data = {"sub": "test@example.com"}

        # Manually create expired token
        to_encode = data.copy()
        expire = datetime.utcnow() + expired_delta
        to_encode.update({"exp": expire})
        expired_token = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

        verified_email = verify_token(expired_token)
        assert verified_email is None

    def test_verify_token_no_subject(self):
        """
        Test token verification with token missing subject.

        Verifies:
        - Token without 'sub' field returns None
        - Required fields are properly validated
        """
        data = {"user_id": 123}  # Missing 'sub' field
        token = create_access_token(data)

        verified_email = verify_token(token)
        assert verified_email is None


class TestUserDatabaseOperations:
    """Test suite for user database operations."""

    def test_get_user_by_email_existing_user(self, test_session, sample_user):
        """
        Test retrieving existing user by email.

        Verifies:
        - Existing user is found
        - Correct user data is returned
        """
        user = get_user_by_email(test_session, sample_user.email)

        assert user is not None
        assert user.id == sample_user.id
        assert user.email == sample_user.email
        assert user.username == sample_user.username

    def test_get_user_by_email_nonexistent_user(self, test_session):
        """
        Test retrieving nonexistent user by email.

        Verifies:
        - Nonexistent user returns None
        - No exceptions are raised
        """
        user = get_user_by_email(test_session, "nonexistent@example.com")

        assert user is None

    def test_get_user_by_username_existing_user(self, test_session, sample_user):
        """
        Test retrieving existing user by username.

        Verifies:
        - Existing user is found by username
        - Correct user data is returned
        """
        user = get_user_by_username(test_session, sample_user.username)

        assert user is not None
        assert user.id == sample_user.id
        assert user.email == sample_user.email
        assert user.username == sample_user.username

    def test_get_user_by_username_nonexistent_user(self, test_session):
        """
        Test retrieving nonexistent user by username.

        Verifies:
        - Nonexistent user returns None
        - No exceptions are raised
        """
        user = get_user_by_username(test_session, "nonexistentuser")

        assert user is None

    def test_get_user_by_email_case_sensitivity(self, test_session, sample_user):
        """
        Test email lookup case sensitivity.

        Verifies:
        - Email lookup behavior with different cases
        - Database query case handling
        """
        # Test with different case
        user = get_user_by_email(test_session, sample_user.email.upper())

        # This depends on database collation settings
        # SQLite is case-insensitive by default for LIKE but case-sensitive for =
        # This test documents the behavior
        assert user is None or user.email.lower() == sample_user.email.lower()


class TestUserAuthentication:
    """Test suite for user authentication."""

    def test_authenticate_user_correct_credentials(
        self, test_session, sample_user, sample_user_data
    ):
        """
        Test authentication with correct credentials.

        Verifies:
        - Correct email and password return user
        - User object is complete and correct
        """
        user = authenticate_user(
            test_session, sample_user_data["email"], sample_user_data["password"]
        )

        assert user is not None
        assert user.id == sample_user.id
        assert user.email == sample_user.email

    def test_authenticate_user_wrong_password(self, test_session, sample_user):
        """
        Test authentication with wrong password.

        Verifies:
        - Wrong password returns None
        - User is not authenticated with incorrect credentials
        """
        user = authenticate_user(test_session, sample_user.email, "wrongpassword")

        assert user is None

    def test_authenticate_user_nonexistent_email(self, test_session):
        """
        Test authentication with nonexistent email.

        Verifies:
        - Nonexistent email returns None
        - No exceptions are raised for invalid users
        """
        user = authenticate_user(test_session, "nonexistent@example.com", "anypassword")

        assert user is None

    def test_authenticate_user_empty_credentials(self, test_session):
        """
        Test authentication with empty credentials.

        Verifies:
        - Empty email/password combinations are rejected
        - Function handles edge cases gracefully
        """
        # Test empty email
        user = authenticate_user(test_session, "", "password")
        assert user is None

        # Test empty password
        user = authenticate_user(test_session, "test@example.com", "")
        assert user is None


class TestCurrentUserAuthentication:
    """Test suite for current user authentication via JWT."""

    def test_get_current_user_valid_token(self, test_session, sample_user):
        """
        Test retrieving current user with valid token.

        Verifies:
        - Valid token returns correct user
        - User data is complete
        """
        # Create valid token
        token = create_access_token({"sub": sample_user.email})
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)

        user = get_current_user(credentials, test_session)

        assert user is not None
        assert user.id == sample_user.id
        assert user.email == sample_user.email

    def test_get_current_user_invalid_token(self, test_session):
        """
        Test current user authentication with invalid token.

        Verifies:
        - Invalid token raises HTTPException
        - Exception has correct status code and message
        """
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer", credentials="invalid.token.here"
        )

        with pytest.raises(HTTPException) as exc_info:
            get_current_user(credentials, test_session)

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Could not validate credentials" in exc_info.value.detail

    def test_get_current_user_token_for_nonexistent_user(self, test_session):
        """
        Test current user authentication with token for nonexistent user.

        Verifies:
        - Valid token for nonexistent user raises HTTPException
        - Exception indicates user not found
        """
        # Create token for nonexistent user
        token = create_access_token({"sub": "nonexistent@example.com"})
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)

        with pytest.raises(HTTPException) as exc_info:
            get_current_user(credentials, test_session)

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert "User not found" in exc_info.value.detail

    def test_get_current_user_expired_token(self, test_session, sample_user):
        """
        Test current user authentication with expired token.

        Verifies:
        - Expired token raises HTTPException
        - Expiration is properly enforced
        """
        # Create expired token
        expired_delta = timedelta(minutes=-1)
        data = {"sub": sample_user.email}
        to_encode = data.copy()
        expire = datetime.utcnow() + expired_delta
        to_encode.update({"exp": expire})
        expired_token = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer", credentials=expired_token
        )

        with pytest.raises(HTTPException) as exc_info:
            get_current_user(credentials, test_session)

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED


class TestSecurityConfiguration:
    """Test suite for security configuration and constants."""

    def test_security_constants(self):
        """
        Test security configuration constants.

        Verifies:
        - Security constants are properly defined
        - Values are appropriate for production use
        """
        assert isinstance(SECRET_KEY, str)
        assert len(SECRET_KEY) > 10  # Should be substantial length
        assert ALGORITHM == "HS256"
        assert isinstance(ACCESS_TOKEN_EXPIRE_MINUTES, int)
        assert ACCESS_TOKEN_EXPIRE_MINUTES > 0

    def test_bcrypt_context_configuration(self):
        """
        Test bcrypt context configuration.

        Verifies:
        - Bcrypt is properly configured
        - Deprecated algorithms are handled
        """
        from auth import pwd_context

        assert "bcrypt" in pwd_context.schemes()
        assert pwd_context.deprecated == "auto"

    def test_http_bearer_security(self):
        """
        Test HTTP Bearer security configuration.

        Verifies:
        - HTTPBearer is properly configured
        - Security scheme is available
        """
        from auth import security

        assert security is not None
        assert hasattr(security, "__call__")


class TestAuthenticationIntegration:
    """Test suite for authentication integration scenarios."""

    def test_full_authentication_flow(
        self, test_session, sample_user, sample_user_data
    ):
        """
        Test complete authentication flow from login to token verification.

        Verifies:
        - End-to-end authentication process
        - Token generation and verification
        - User retrieval from token
        """
        # 1. Authenticate user
        user = authenticate_user(
            test_session, sample_user_data["email"], sample_user_data["password"]
        )
        assert user is not None

        # 2. Create token
        token = create_access_token({"sub": user.email})
        assert token is not None

        # 3. Verify token
        verified_email = verify_token(token)
        assert verified_email == user.email

        # 4. Get current user from token
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
        current_user = get_current_user(credentials, test_session)
        assert current_user.id == user.id

    def test_token_refresh_scenario(self, test_session, sample_user):
        """
        Test token refresh scenario.

        Verifies:
        - New tokens can be generated for authenticated users
        - Multiple tokens work independently
        """
        # Generate first token
        token1 = create_access_token({"sub": sample_user.email})

        # Generate second token
        token2 = create_access_token({"sub": sample_user.email})

        # Both tokens should be valid
        assert verify_token(token1) == sample_user.email
        assert verify_token(token2) == sample_user.email

        # Tokens should be different
        assert token1 != token2

    def test_concurrent_user_authentication(self, test_session):
        """
        Test authentication with multiple users.

        Verifies:
        - Multiple users can be authenticated simultaneously
        - Tokens don't interfere with each other
        """
        from database import User

        # Create multiple users
        users_data = [
            {"email": "user1@example.com", "username": "user1", "password": "pass1"},
            {"email": "user2@example.com", "username": "user2", "password": "pass2"},
        ]

        users = []
        tokens = []

        for user_data in users_data:
            user = User(
                email=user_data["email"],
                username=user_data["username"],
                hashed_password=hash_password(user_data["password"]),
            )
            test_session.add(user)
            users.append(user)

        test_session.commit()

        # Authenticate all users and create tokens
        for i, user in enumerate(users):
            authenticated = authenticate_user(
                test_session, users_data[i]["email"], users_data[i]["password"]
            )
            assert authenticated is not None

            token = create_access_token({"sub": user.email})
            tokens.append(token)

        # Verify all tokens work correctly
        for i, token in enumerate(tokens):
            verified_email = verify_token(token)
            assert verified_email == users[i].email
