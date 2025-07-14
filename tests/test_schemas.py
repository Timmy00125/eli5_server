"""
Tests for schemas.py - Pydantic data validation and serialization.
Tests request/response models, validation rules, and data transformation.
"""

import pytest
from datetime import datetime
from pydantic import ValidationError

from schemas import (
    UserRegistration,
    UserLogin,
    UserResponse,
    TokenResponse,
    ConceptResponse,
    HistoryEntryResponse,
    HistoryListResponse,
    SaveHistoryRequest,
    MessageResponse,
    ErrorResponse,
)


class TestUserRegistrationSchema:
    """Test suite for UserRegistration schema."""

    def test_valid_user_registration(self):
        """
        Test valid user registration data.

        Verifies:
        - Valid data is accepted
        - All fields are properly set
        - Field types are correct
        """
        data = {
            "email": "test@example.com",
            "username": "testuser",
            "password": "password123",
        }

        registration = UserRegistration(**data)

        assert registration.email == data["email"]
        assert registration.username == data["username"]
        assert registration.password == data["password"]

    def test_invalid_email_format(self):
        """
        Test user registration with invalid email format.

        Verifies:
        - Invalid email formats are rejected
        - Appropriate validation error is raised
        """
        data = {
            "email": "invalid-email",
            "username": "testuser",
            "password": "password123",
        }

        with pytest.raises(ValidationError) as exc_info:
            UserRegistration(**data)

        errors = exc_info.value.errors()
        assert any("email" in str(error).lower() for error in errors)

    def test_username_too_short(self):
        """
        Test user registration with username too short.

        Verifies:
        - Usernames below minimum length are rejected
        - Validation error indicates length requirement
        """
        data = {
            "email": "test@example.com",
            "username": "ab",  # Too short (minimum 3)
            "password": "password123",
        }

        with pytest.raises(ValidationError) as exc_info:
            UserRegistration(**data)

        errors = exc_info.value.errors()
        assert any("username" in error.get("loc", []) for error in errors)

    def test_username_too_long(self):
        """
        Test user registration with username too long.

        Verifies:
        - Usernames above maximum length are rejected
        - Validation error indicates length requirement
        """
        data = {
            "email": "test@example.com",
            "username": "a" * 51,  # Too long (maximum 50)
            "password": "password123",
        }

        with pytest.raises(ValidationError) as exc_info:
            UserRegistration(**data)

        errors = exc_info.value.errors()
        assert any("username" in error.get("loc", []) for error in errors)

    def test_password_too_short(self):
        """
        Test user registration with password too short.

        Verifies:
        - Passwords below minimum length are rejected
        - Validation error indicates length requirement
        """
        data = {
            "email": "test@example.com",
            "username": "testuser",
            "password": "123",  # Too short (minimum 6)
        }

        with pytest.raises(ValidationError) as exc_info:
            UserRegistration(**data)

        errors = exc_info.value.errors()
        assert any("password" in error.get("loc", []) for error in errors)

    def test_missing_required_fields(self):
        """
        Test user registration with missing required fields.

        Verifies:
        - All required fields must be provided
        - Validation errors indicate missing fields
        """
        # Test missing email
        with pytest.raises(ValidationError):
            UserRegistration(username="testuser", password="password123")

        # Test missing username
        with pytest.raises(ValidationError):
            UserRegistration(email="test@example.com", password="password123")

        # Test missing password
        with pytest.raises(ValidationError):
            UserRegistration(email="test@example.com", username="testuser")

    def test_field_descriptions(self):
        """
        Test that field descriptions are properly set.

        Verifies:
        - Field descriptions provide helpful information
        - Schema documentation is available
        """
        schema = UserRegistration.model_json_schema()
        properties = schema.get("properties", {})

        assert "description" in properties.get("email", {})
        assert "description" in properties.get("username", {})
        assert "description" in properties.get("password", {})


class TestUserLoginSchema:
    """Test suite for UserLogin schema."""

    def test_valid_user_login(self):
        """
        Test valid user login data.

        Verifies:
        - Valid login data is accepted
        - All fields are properly set
        """
        data = {"email": "test@example.com", "password": "password123"}

        login = UserLogin(**data)

        assert login.email == data["email"]
        assert login.password == data["password"]

    def test_invalid_login_email(self):
        """
        Test user login with invalid email format.

        Verifies:
        - Invalid email formats are rejected in login
        """
        data = {"email": "invalid-email", "password": "password123"}

        with pytest.raises(ValidationError):
            UserLogin(**data)

    def test_missing_login_fields(self):
        """
        Test user login with missing fields.

        Verifies:
        - Both email and password are required for login
        """
        # Test missing email
        with pytest.raises(ValidationError):
            UserLogin(password="password123")

        # Test missing password
        with pytest.raises(ValidationError):
            UserLogin(email="test@example.com")


class TestUserResponseSchema:
    """Test suite for UserResponse schema."""

    def test_valid_user_response(self):
        """
        Test valid user response data.

        Verifies:
        - User response data is properly formatted
        - Datetime fields are handled correctly
        """
        data = {
            "id": 1,
            "email": "test@example.com",
            "username": "testuser",
            "created_at": datetime.now(),
        }

        response = UserResponse(**data)

        assert response.id == data["id"]
        assert response.email == data["email"]
        assert response.username == data["username"]
        assert response.created_at == data["created_at"]

    def test_user_response_from_orm(self, sample_user):
        """
        Test UserResponse creation from ORM model.

        Verifies:
        - ORM models can be converted to response schemas
        - from_attributes configuration works
        """
        response = UserResponse.model_validate(sample_user)

        assert response.id == sample_user.id
        assert response.email == sample_user.email
        assert response.username == sample_user.username
        assert response.created_at == sample_user.created_at

    def test_user_response_missing_fields(self):
        """
        Test UserResponse with missing required fields.

        Verifies:
        - All required fields must be provided
        """
        with pytest.raises(ValidationError):
            UserResponse(
                email="test@example.com",
                username="testuser",
                created_at=datetime.now(),
                # Missing id
            )


class TestTokenResponseSchema:
    """Test suite for TokenResponse schema."""

    def test_valid_token_response(self):
        """
        Test valid token response data.

        Verifies:
        - Token response includes all required fields
        - Default token_type is set correctly
        """
        user_data = {
            "id": 1,
            "email": "test@example.com",
            "username": "testuser",
            "created_at": datetime.now(),
        }
        user_response = UserResponse(**user_data)

        token_data = {"access_token": "sample.jwt.token", "user": user_response}

        token_response = TokenResponse(**token_data)

        assert token_response.access_token == token_data["access_token"]
        assert token_response.token_type == "bearer"  # Default value
        assert token_response.user == user_response

    def test_custom_token_type(self):
        """
        Test token response with custom token type.

        Verifies:
        - Token type can be customized
        - Custom values override defaults
        """
        user_data = {
            "id": 1,
            "email": "test@example.com",
            "username": "testuser",
            "created_at": datetime.now(),
        }
        user_response = UserResponse(**user_data)

        token_data = {
            "access_token": "sample.jwt.token",
            "token_type": "custom",
            "user": user_response,
        }

        token_response = TokenResponse(**token_data)

        assert token_response.token_type == "custom"


class TestConceptResponseSchema:
    """Test suite for ConceptResponse schema."""

    def test_valid_concept_response(self):
        """
        Test valid concept response data.

        Verifies:
        - Concept and explanation are properly stored
        - String fields work correctly
        """
        data = {
            "concept": "Algorithm",
            "explanation": "A step-by-step procedure for solving problems",
        }

        response = ConceptResponse(**data)

        assert response.concept == data["concept"]
        assert response.explanation == data["explanation"]

    def test_concept_response_empty_strings(self):
        """
        Test concept response with empty strings.

        Verifies:
        - Empty strings are allowed (if that's the intended behavior)
        """
        data = {"concept": "", "explanation": ""}

        response = ConceptResponse(**data)

        assert response.concept == ""
        assert response.explanation == ""

    def test_concept_response_missing_fields(self):
        """
        Test concept response with missing fields.

        Verifies:
        - Both concept and explanation are required
        """
        with pytest.raises(ValidationError):
            ConceptResponse(concept="Algorithm")  # Missing explanation

        with pytest.raises(ValidationError):
            ConceptResponse(explanation="Test explanation")  # Missing concept


class TestHistoryEntryResponseSchema:
    """Test suite for HistoryEntryResponse schema."""

    def test_valid_history_entry_response(self):
        """
        Test valid history entry response data.

        Verifies:
        - All fields are properly stored
        - Datetime handling works correctly
        """
        data = {
            "id": 1,
            "concept": "Variable",
            "explanation": "Storage location for data",
            "created_at": datetime.now(),
        }

        response = HistoryEntryResponse(**data)

        assert response.id == data["id"]
        assert response.concept == data["concept"]
        assert response.explanation == data["explanation"]
        assert response.created_at == data["created_at"]

    def test_history_entry_response_from_orm(self, sample_history_entry):
        """
        Test HistoryEntryResponse creation from ORM model.

        Verifies:
        - ORM models can be converted to response schemas
        - from_attributes configuration works
        """
        response = HistoryEntryResponse.model_validate(sample_history_entry)

        assert response.id == sample_history_entry.id
        assert response.concept == sample_history_entry.concept
        assert response.explanation == sample_history_entry.explanation
        assert response.created_at == sample_history_entry.created_at


class TestHistoryListResponseSchema:
    """Test suite for HistoryListResponse schema."""

    def test_valid_history_list_response(self):
        """
        Test valid history list response data.

        Verifies:
        - List of entries and total count work correctly
        - Empty lists are handled properly
        """
        entry_data = {
            "id": 1,
            "concept": "Algorithm",
            "explanation": "Step by step",
            "created_at": datetime.now(),
        }
        entry = HistoryEntryResponse(**entry_data)

        data = {"entries": [entry], "total": 1}

        response = HistoryListResponse(**data)

        assert len(response.entries) == 1
        assert response.total == 1
        assert response.entries[0] == entry

    def test_empty_history_list_response(self):
        """
        Test history list response with empty entries.

        Verifies:
        - Empty lists are properly handled
        - Zero total count works correctly
        """
        data = {"entries": [], "total": 0}

        response = HistoryListResponse(**data)

        assert len(response.entries) == 0
        assert response.total == 0


class TestSaveHistoryRequestSchema:
    """Test suite for SaveHistoryRequest schema."""

    def test_valid_save_history_request(self):
        """
        Test valid save history request data.

        Verifies:
        - Request data is properly validated
        - All required fields are present
        """
        data = {"concept": "Function", "explanation": "A reusable block of code"}

        request = SaveHistoryRequest(**data)

        assert request.concept == data["concept"]
        assert request.explanation == data["explanation"]

    def test_save_history_request_missing_fields(self):
        """
        Test save history request with missing fields.

        Verifies:
        - Both concept and explanation are required
        """
        with pytest.raises(ValidationError):
            SaveHistoryRequest(concept="Function")  # Missing explanation

        with pytest.raises(ValidationError):
            SaveHistoryRequest(explanation="Test explanation")  # Missing concept

    def test_save_history_request_field_descriptions(self):
        """
        Test field descriptions in SaveHistoryRequest.

        Verifies:
        - Field descriptions provide helpful information
        """
        schema = SaveHistoryRequest.model_json_schema()
        properties = schema.get("properties", {})

        assert "description" in properties.get("concept", {})
        assert "description" in properties.get("explanation", {})


class TestMessageResponseSchema:
    """Test suite for MessageResponse schema."""

    def test_valid_message_response(self):
        """
        Test valid message response data.

        Verifies:
        - Message and success fields work correctly
        - Default success value is True
        """
        data = {"message": "Operation completed successfully"}

        response = MessageResponse(**data)

        assert response.message == data["message"]
        assert response.success is True  # Default value

    def test_message_response_custom_success(self):
        """
        Test message response with custom success value.

        Verifies:
        - Success value can be overridden
        """
        data = {"message": "Operation failed", "success": False}

        response = MessageResponse(**data)

        assert response.message == data["message"]
        assert response.success is False

    def test_message_response_missing_message(self):
        """
        Test message response with missing message.

        Verifies:
        - Message field is required
        """
        with pytest.raises(ValidationError):
            MessageResponse(success=True)  # Missing message


class TestErrorResponseSchema:
    """Test suite for ErrorResponse schema."""

    def test_valid_error_response(self):
        """
        Test valid error response data.

        Verifies:
        - Error detail and success fields work correctly
        - Default success value is False
        """
        data = {"detail": "An error occurred"}

        response = ErrorResponse(**data)

        assert response.detail == data["detail"]
        assert response.success is False  # Default value

    def test_error_response_custom_success(self):
        """
        Test error response with custom success value.

        Verifies:
        - Success value can be overridden (though unusual for errors)
        """
        data = {"detail": "Warning message", "success": True}

        response = ErrorResponse(**data)

        assert response.detail == data["detail"]
        assert response.success is True

    def test_error_response_missing_detail(self):
        """
        Test error response with missing detail.

        Verifies:
        - Detail field is required
        """
        with pytest.raises(ValidationError):
            ErrorResponse(success=False)  # Missing detail


class TestSchemaIntegration:
    """Test suite for schema integration scenarios."""

    def test_nested_schema_validation(self):
        """
        Test validation of nested schemas.

        Verifies:
        - Nested schemas validate correctly
        - Complex data structures work
        """
        # Create nested data for TokenResponse
        user_data = {
            "id": 1,
            "email": "test@example.com",
            "username": "testuser",
            "created_at": datetime.now(),
        }

        token_data = {
            "access_token": "sample.jwt.token",
            "user": user_data,  # Nested user data
        }

        token_response = TokenResponse(**token_data)

        assert isinstance(token_response.user, UserResponse)
        assert token_response.user.email == user_data["email"]

    def test_schema_json_serialization(self):
        """
        Test JSON serialization of schemas.

        Verifies:
        - Schemas can be serialized to JSON
        - Datetime fields are properly handled
        """
        data = {"concept": "Algorithm", "explanation": "Step by step procedure"}

        response = ConceptResponse(**data)
        json_data = response.model_dump()

        assert json_data["concept"] == data["concept"]
        assert json_data["explanation"] == data["explanation"]

    def test_schema_validation_edge_cases(self):
        """
        Test schema validation with edge cases.

        Verifies:
        - Unusual but valid data is handled
        - Edge cases don't break validation
        """
        # Test with very long strings
        long_string = "a" * 1000
        data = {"concept": "Long Concept", "explanation": long_string}

        response = ConceptResponse(**data)
        assert response.explanation == long_string

        # Test with special characters
        special_data = {
            "concept": "Special!@#$%^&*()",
            "explanation": "Unicode: 🚀 emoji test",
        }

        special_response = ConceptResponse(**special_data)
        assert special_response.concept == special_data["concept"]
        assert special_response.explanation == special_data["explanation"]

    def test_schema_type_coercion(self):
        """
        Test type coercion in schemas.

        Verifies:
        - Pydantic type coercion works correctly
        - String to int conversion for IDs
        """
        # Test ID as string (should be coerced to int)
        data = {
            "id": "123",  # String that should become int
            "email": "test@example.com",
            "username": "testuser",
            "created_at": datetime.now(),
        }

        response = UserResponse(**data)
        assert response.id == 123
        assert isinstance(response.id, int)

    def test_schema_validation_error_details(self):
        """
        Test detailed validation error information.

        Verifies:
        - Validation errors provide useful details
        - Error locations are accurate
        """
        try:
            UserRegistration(email="invalid", username="", password="")
        except ValidationError as e:
            errors = e.errors()

            # Should have multiple validation errors
            assert len(errors) > 1

            # Each error should have location and message
            for error in errors:
                assert "loc" in error
                assert "msg" in error
                assert "type" in error
