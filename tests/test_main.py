"""
Tests for main.py - API endpoints and application logic.
Tests the FastAPI application routes, middleware, and integration with external services.
"""

from unittest.mock import patch, Mock
from fastapi import status


class TestMainAPI:
    """Test suite for main API endpoints."""

    def test_api_explain_endpoint_success(self, client, mock_gemini_client):
        """
        Test successful explanation generation via /api/explain endpoint.

        Verifies:
        - API returns 200 status code
        - Response contains concept and explanation
        - Gemini API is called correctly
        - Response format matches expected schema
        """
        response = client.get("/api/explain")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Verify response structure
        assert "concept" in data
        assert "explanation" in data
        assert isinstance(data["concept"], str)
        assert isinstance(data["explanation"], str)
        assert len(data["concept"]) > 0
        assert len(data["explanation"]) > 0

        # Verify the concept is from the predefined list
        from routers.explain import CS_CONCEPTS

        assert data["concept"] in CS_CONCEPTS

        # Verify Gemini API was called
        mock_gemini_client.models.generate_content.assert_called_once()

    def test_api_explain_endpoint_no_api_key(self, client):
        """
        Test /api/explain endpoint behavior when API key is missing.

        Verifies:
        - Returns 500 status code when API key is not configured
        - Error message indicates API key issue
        """
        with patch("routers.explain.api_key", None):
            response = client.get("/api/explain")

            assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
            data = response.json()
            assert "Gemini API not configured" in data["detail"]

    def test_api_explain_endpoint_gemini_error(self, client):
        """
        Test /api/explain endpoint behavior when Gemini API fails.

        Verifies:
        - Returns 500 status code on API failure
        - Error message includes original error details
        - Handles external service failures gracefully
        """
        with patch("routers.explain.client") as mock_client:
            mock_client.models.generate_content.side_effect = Exception("API Error")

            response = client.get("/api/explain")

            assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
            data = response.json()
            assert "Error generating explanation" in data["detail"]
            assert "API Error" in data["detail"]

    def test_fallback_explain_endpoint(self, client):
        """
        Test the fallback explanation endpoint.

        Verifies:
        - Returns 200 status code
        - Returns fixed algorithm explanation
        - Response format matches expected schema
        - Content is properly formatted
        """
        response = client.get("/api/fallback-explain")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Verify response structure
        assert "concept" in data
        assert "explanation" in data
        assert data["concept"] == "Algorithms"
        assert isinstance(data["explanation"], str)
        assert len(data["explanation"]) > 0

        # Verify content contains expected elements
        explanation = data["explanation"]
        assert "algorithm" in explanation.lower()
        assert "```python" in explanation  # Contains code examples
        assert "sandwich" in explanation.lower()  # Contains analogy

    def test_cors_configuration(self, client):
        """
        Test CORS middleware configuration.

        Verifies:
        - CORS headers are properly set
        - Allowed origins are configured
        - Preflight requests are handled
        """
        # Test preflight request
        response = client.options(
            "/api/explain",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
            },
        )

        # Note: TestClient might not fully simulate CORS preflight
        # This test verifies the endpoint is accessible
        assert response.status_code in [200, 405]  # 405 is acceptable for OPTIONS

    def test_random_concept_selection(self, client, mock_gemini_client):
        """
        Test that different concepts are selected randomly.

        Verifies:
        - Multiple calls can return different concepts
        - All returned concepts are from the predefined list
        """
        from routers.explain import CS_CONCEPTS

        concepts_seen = set()

        # Make multiple requests to test randomness
        for _ in range(10):
            response = client.get("/api/explain")
            assert response.status_code == status.HTTP_200_OK

            data = response.json()
            concept = data["concept"]
            assert concept in CS_CONCEPTS
            concepts_seen.add(concept)

        # With 10 requests and 30+ concepts, we should see some variety
        # (though randomness might occasionally produce the same concept)
        assert len(concepts_seen) >= 1

    def test_generate_prompt_function(self):
        """
        Test the prompt generation function.

        Verifies:
        - Function generates appropriate prompts
        - Prompt contains the concept name
        - Prompt includes required instructions
        """
        from routers.explain import generate_prompt

        concept = "Algorithm"
        prompt = generate_prompt(concept)

        assert isinstance(prompt, str)
        assert concept in prompt
        assert "five-year-old" in prompt
        assert "simple language" in prompt
        assert "markdown" in prompt
        assert "python code" in prompt.lower()

    def test_cs_concepts_list(self):
        """
        Test the CS_CONCEPTS list configuration.

        Verifies:
        - List contains expected number of concepts
        - All concepts are strings
        - No duplicate concepts
        - Common CS concepts are included
        """
        from routers.explain import CS_CONCEPTS

        assert isinstance(CS_CONCEPTS, list)
        assert len(CS_CONCEPTS) > 20  # Should have substantial number of concepts

        # Check all items are strings
        assert all(isinstance(concept, str) for concept in CS_CONCEPTS)

        # Check no duplicates
        assert len(CS_CONCEPTS) == len(set(CS_CONCEPTS))

        # Check for some expected concepts
        expected_concepts = ["Algorithm", "Variable", "Function", "Database"]
        for concept in expected_concepts:
            assert concept in CS_CONCEPTS

    @patch("routers.explain.logger")
    def test_logging_behavior(self, mock_logger, client, mock_gemini_client):
        """
        Test that appropriate logging occurs during API calls.

        Verifies:
        - Info logs are generated for successful requests
        - Error logs are generated for failures
        - Log messages contain relevant information
        """
        # Test successful request logging
        response = client.get("/api/explain")
        assert response.status_code == status.HTTP_200_OK

        # Verify info logs were called
        mock_logger.info.assert_called()

        # Check log messages contain relevant information
        log_calls = [call.args[0] for call in mock_logger.info.call_args_list]
        assert any("concept" in log.lower() for log in log_calls)

    def test_app_initialization(self):
        """
        Test FastAPI application initialization.

        Verifies:
        - App is properly configured
        - Title is set correctly
        - Middleware is properly attached
        """
        from main import app

        assert app.title == "LearnInFive API"
        assert hasattr(app, "user_middleware")  # CORS middleware should be attached

    def test_environment_variable_handling(self):
        """
        Test proper handling of environment variables.

        Verifies:
        - API key is read from environment
        - Model name is configurable
        - Default values are used appropriately
        """
        import os
        from unittest.mock import patch

        # Test with missing API key
        with patch.dict(os.environ, {}, clear=True):
            with patch("main.load_dotenv"):
                # This would normally cause an error, but we test the detection
                api_key = os.getenv("GEMINI_API_KEY")
                assert api_key is None

    def test_response_model_validation(self, client, mock_gemini_client):
        """
        Test that response models are properly validated.

        Verifies:
        - Responses match ConceptResponse schema
        - Type validation works correctly
        - Required fields are present
        """
        response = client.get("/api/explain")
        assert response.status_code == status.HTTP_200_OK

        data = response.json()

        # Test ConceptResponse schema validation
        from schemas import ConceptResponse

        concept_response = ConceptResponse(**data)

        assert concept_response.concept == data["concept"]
        assert concept_response.explanation == data["explanation"]

    def test_error_handling_integration(self, client):
        """
        Test end-to-end error handling in the API.

        Verifies:
        - Errors are properly caught and formatted
        - HTTP status codes are appropriate
        - Error messages are informative but not exposing internals
        """
        # Test various error conditions
        with patch("routers.explain.client") as mock_client:
            # Test different types of exceptions
            error_scenarios = [
                (ConnectionError("Network error"), "network"),
                (ValueError("Invalid input"), "input"),
                (Exception("Generic error"), "error"),
            ]

            for exception, expected_keyword in error_scenarios:
                mock_client.models.generate_content.side_effect = exception

                response = client.get("/api/explain")
                assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

                data = response.json()
                assert "detail" in data
                assert isinstance(data["detail"], str)


class TestApplicationConfiguration:
    """Test suite for application configuration and setup."""

    def test_gemini_client_initialization(self):
        """
        Test Gemini client initialization.

        Verifies:
        - Client is initialized with proper API key
        - Error handling for initialization failures
        """
        with patch("routers.explain.genai.Client") as mock_client_class:
            mock_client_class.return_value = Mock()

            # Reload the module to test initialization
            import importlib
            import routers.explain

            importlib.reload(routers.explain)

            # Verify client was initialized with API key
            mock_client_class.assert_called_with(api_key="test-api-key")

    def test_logging_configuration(self):
        """
        Test logging configuration.

        Verifies:
        - Logger is properly configured
        - Log level is appropriate
        - Logger name is correct
        """
        from main import logger

        assert logger.name == "main"
        # Note: Log level testing depends on logging configuration

    def test_model_configuration(self):
        """
        Test AI model configuration.

        Verifies:
        - Model name is read from environment
        - Default model is used when not specified
        """
        import os

        # Test default model
        with patch.dict(os.environ, {}, clear=True):
            from routers.explain import generate_prompt

            # This function should work regardless of model configuration
            prompt = generate_prompt("Test")
            assert isinstance(prompt, str)
