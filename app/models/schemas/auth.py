"""Authentication request and response schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr


class RegisterRequest(BaseModel):
    """User registration payload."""

    email: EmailStr
    password: str


class LoginRequest(BaseModel):
    """User login payload."""

    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """JWT token pair returned on login/register."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    """Refresh token exchange payload."""

    refresh_token: str


class UserResponse(BaseModel):
    """Public user representation."""

    id: UUID
    email: str
    created_at: datetime
