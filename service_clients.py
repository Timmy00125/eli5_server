"""
HTTP clients for communicating with other microservices.
"""

import httpx
import os
import logging
from typing import Optional, Dict, Any
from fastapi import HTTPException
import json

logger = logging.getLogger(__name__)


class ServiceConfig:
    """Configuration for microservice endpoints."""

    def __init__(self):
        # Service URLs from environment variables or defaults for local development
        self.auth_service_url = os.getenv("AUTH_SERVICE_URL", "http://localhost:8001")
        self.history_service_url = os.getenv(
            "HISTORY_SERVICE_URL", "http://localhost:8002"
        )

        # HTTP client timeout settings
        self.timeout = float(os.getenv("HTTP_TIMEOUT", "30.0"))
        self.max_retries = int(os.getenv("HTTP_MAX_RETRIES", "3"))


config = ServiceConfig()


class BaseServiceClient:
    """Base class for all service clients with common HTTP functionality."""

    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")
        self.client = httpx.AsyncClient(
            timeout=config.timeout,
            limits=httpx.Limits(max_keepalive_connections=5, max_connections=10),
        )

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        headers: Optional[Dict[str, str]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
    ) -> httpx.Response:
        """Make HTTP request with error handling and retries."""
        url = f"{self.base_url}{endpoint}"
        request_headers = headers or {}

        for attempt in range(config.max_retries):
            try:
                logger.info(f"Making {method} request to {url} (attempt {attempt + 1})")

                response = await self.client.request(
                    method=method,
                    url=url,
                    headers=request_headers,
                    json=json_data,
                    data=data,
                )

                # Log response details
                logger.info(f"Response status: {response.status_code} for {url}")

                if response.status_code < 500:
                    # Don't retry client errors (4xx), only server errors (5xx)
                    return response

            except (httpx.ConnectError, httpx.TimeoutException) as e:
                logger.warning(f"Request attempt {attempt + 1} failed: {str(e)}")
                if attempt == config.max_retries - 1:
                    raise HTTPException(
                        status_code=503, detail=f"Service unavailable: {self.base_url}"
                    )
            except Exception as e:
                logger.error(f"Unexpected error in request: {str(e)}")
                raise HTTPException(
                    status_code=500,
                    detail=f"Internal error communicating with service: {str(e)}",
                )

        # This should never be reached due to the raise in the loop
        raise HTTPException(status_code=503, detail="Service communication failed")

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()


class AuthServiceClient(BaseServiceClient):
    """Client for communicating with the Authentication Service."""

    def __init__(self):
        super().__init__(config.auth_service_url)

    async def validate_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Validate a JWT token with the auth service.
        Returns user data if token is valid, None otherwise.
        """
        try:
            headers = {"Authorization": f"Bearer {token}"}
            response = await self._make_request("GET", "/auth/me", headers=headers)

            if response.status_code == 200:
                return response.json()
            elif response.status_code == 401:
                logger.warning("Token validation failed: unauthorized")
                return None
            else:
                logger.error(f"Auth service error: {response.status_code}")
                return None

        except Exception as e:
            logger.error(f"Error validating token: {str(e)}")
            return None

    async def create_user(
        self, username: str, email: str, password: str
    ) -> Optional[Dict[str, Any]]:
        """Create a new user via the auth service."""
        try:
            user_data = {"username": username, "email": email, "password": password}

            response = await self._make_request(
                "POST", "/auth/signup", json_data=user_data
            )

            if response.status_code == 200:
                return response.json()
            else:
                error_detail = response.json().get("detail", "Unknown error")
                logger.error(f"User creation failed: {error_detail}")
                raise HTTPException(
                    status_code=response.status_code, detail=error_detail
                )

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error creating user: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to create user")

    async def login_user(self, email: str, password: str) -> Optional[Dict[str, Any]]:
        """Login user and get access token."""
        try:
            # OAuth2PasswordRequestForm expects form data
            form_data = {
                "username": email,  # Auth service uses username field for email
                "password": password,
            }

            response = await self._make_request("POST", "/auth/login", data=form_data)

            if response.status_code == 200:
                return response.json()
            else:
                error_detail = response.json().get("detail", "Invalid credentials")
                logger.warning(f"Login failed: {error_detail}")
                raise HTTPException(
                    status_code=response.status_code, detail=error_detail
                )

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error during login: {str(e)}")
            raise HTTPException(status_code=500, detail="Login failed")


class HistoryServiceClient(BaseServiceClient):
    """Client for communicating with the History Service."""

    def __init__(self):
        super().__init__(config.history_service_url)

    async def add_history_record(
        self, token: str, concept_details: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Add a history record for the authenticated user."""
        try:
            headers = {"Authorization": f"Bearer {token}"}
            record_data = {"concept_details": concept_details}

            response = await self._make_request(
                "POST", "/history/", headers=headers, json_data=record_data
            )

            if response.status_code == 200:
                return response.json()
            else:
                error_detail = response.json().get("detail", "Failed to add history")
                logger.error(f"History creation failed: {error_detail}")
                return None

        except Exception as e:
            logger.error(f"Error adding history record: {str(e)}")
            return None

    async def get_user_history(self, token: str, user_id: int) -> Optional[list]:
        """Get history records for a user."""
        try:
            headers = {"Authorization": f"Bearer {token}"}
            response = await self._make_request(
                "GET", f"/history/{user_id}", headers=headers
            )

            if response.status_code == 200:
                return response.json()
            elif response.status_code == 403:
                logger.warning("Access denied to user history")
                raise HTTPException(status_code=403, detail="Access denied")
            else:
                logger.error(f"Failed to get history: {response.status_code}")
                return None

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting user history: {str(e)}")
            return None


# Global client instances - these will be initialized when the app starts
auth_client = AuthServiceClient()
history_client = HistoryServiceClient()


async def cleanup_clients():
    """Cleanup function to close all HTTP clients."""
    await auth_client.close()
    await history_client.close()
