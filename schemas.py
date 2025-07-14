"""
Pydantic schemas for request and response models.
Defines data validation and serialization for API endpoints.
"""

from datetime import datetime
from typing import List
from pydantic import BaseModel, EmailStr, Field


class UserRegistration(BaseModel):
    """Schema for user registration request."""

    email: EmailStr = Field(..., description="User email address")
    username: str = Field(..., min_length=3, max_length=50, description="Username")
    password: str = Field(..., min_length=6, description="User password")


class UserLogin(BaseModel):
    """Schema for user login request."""

    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., description="User password")


class UserResponse(BaseModel):
    """Schema for user information response."""

    id: int
    email: str
    username: str
    created_at: datetime

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    """Schema for authentication token response."""

    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class ConceptResponse(BaseModel):
    """Schema for concept explanation response."""

    concept: str
    explanation: str


class HistoryEntryResponse(BaseModel):
    """Schema for history entry response."""

    id: int
    concept: str
    explanation: str
    created_at: datetime

    class Config:
        from_attributes = True


class HistoryListResponse(BaseModel):
    """Schema for history list response."""

    entries: List[HistoryEntryResponse]
    total: int


class SaveHistoryRequest(BaseModel):
    """Schema for saving history entry request."""

    concept: str = Field(..., description="Concept name")
    explanation: str = Field(..., description="Concept explanation")


class MessageResponse(BaseModel):
    """Schema for simple message responses."""

    message: str
    success: bool = True


class ErrorResponse(BaseModel):
    """Schema for error responses."""

    detail: str
    success: bool = False
