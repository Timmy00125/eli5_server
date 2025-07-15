"""
Routers for authentication endpoints.
"""

from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from auth import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    authenticate_user,
    create_access_token,
    get_current_user,
)
from database import User, get_db
from schemas import TokenResponse, UserLogin, UserRegistration, UserResponse
from services import UserService

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


@router.post("/register", response_model=TokenResponse)
async def register_user(
    user_data: UserRegistration, db: Session = Depends(get_db)
) -> TokenResponse:
    """
    Register a new user account.

    Creates a new user with email, username, and hashed password.
    Returns access token for immediate login.
    """
    try:
        user: User = UserService.create_user(db, user_data)
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token: str = create_access_token(
            data={"sub": user.email}, expires_delta=access_token_expires
        )
        return TokenResponse(access_token=access_token, user=user)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}",
        )


@router.post("/login", response_model=TokenResponse)
async def login_user(
    user_data: UserLogin, db: Session = Depends(get_db)
) -> TokenResponse:
    """
    Authenticate user and return access token.

    Verifies email and password, returns JWT token for authenticated requests.
    """
    user: User | None = authenticate_user(db, user_data.email, user_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token: str = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )

    return TokenResponse(access_token=access_token, user=user)


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)) -> User:
    """
    Get current authenticated user information.

    Returns user profile data for the authenticated user.
    """
    return current_user
