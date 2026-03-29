from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import Optional

from app.models.user import UserStatus, OAuthProvider


class UserBase(BaseModel):
    """Base user schema with common fields."""
    email: EmailStr
    nickname: Optional[str] = None
    phone_number: Optional[str] = None


class UserCreate(UserBase):
    """Schema for creating a new user."""
    oauth_provider: OAuthProvider
    oauth_id: str
    is_admin: bool = False


class UserUpdate(BaseModel):
    """Schema for updating user information."""
    nickname: Optional[str] = None
    phone_number: Optional[str] = None
    status: Optional[UserStatus] = None


class UserResponse(UserBase):
    """Schema for user response."""
    id: int
    status: UserStatus
    is_admin: bool
    oauth_provider: OAuthProvider
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    """Schema for token response."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds


class OAuthUserInfo(BaseModel):
    """Schema for OAuth user information from providers."""
    oauth_id: str
    email: EmailStr
    nickname: Optional[str] = None
    provider: OAuthProvider
