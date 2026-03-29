from sqlalchemy.orm import Session
from typing import Tuple

from app.models.user import User, UserStatus
from app.schemas.user import OAuthUserInfo, TokenResponse
from app.core.security import create_access_token, create_refresh_token
from app.core.config import settings


class AuthService:
    """Service for authentication-related operations."""

    def __init__(self, db: Session):
        self.db = db

    def create_or_update_user_from_oauth(self, oauth_info: OAuthUserInfo) -> User:
        """
        Create a new user or update existing user from OAuth provider.

        Args:
            oauth_info: OAuth user information

        Returns:
            User object (new or updated)
        """
        # Try to find existing user by OAuth provider and ID
        user = self.db.query(User).filter(
            User.oauth_provider == oauth_info.provider,
            User.oauth_id == oauth_info.oauth_id
        ).first()

        if user:
            # Update existing user
            user.email = oauth_info.email
            if oauth_info.nickname:
                user.nickname = oauth_info.nickname
            user.status = UserStatus.ACTIVE
        else:
            # Create new user
            user = User(
                email=oauth_info.email,
                nickname=oauth_info.nickname,
                oauth_provider=oauth_info.provider,
                oauth_id=oauth_info.oauth_id,
                status=UserStatus.ACTIVE,
                is_admin=False,
            )
            self.db.add(user)

        self.db.commit()
        self.db.refresh(user)

        return user

    def generate_tokens(self, user: User) -> TokenResponse:
        """
        Generate access and refresh tokens for a user.

        Args:
            user: User object

        Returns:
            TokenResponse with tokens
        """
        access_token = create_access_token({"sub": str(user.id)})
        refresh_token = create_refresh_token({"sub": str(user.id)})

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=settings.jwt_access_token_expire_minutes * 60,
        )

    def authenticate_oauth_user(self, oauth_info: OAuthUserInfo) -> TokenResponse:
        """
        Complete OAuth authentication flow.

        Args:
            oauth_info: OAuth user information

        Returns:
            TokenResponse with JWT tokens
        """
        user = self.create_or_update_user_from_oauth(oauth_info)
        return self.generate_tokens(user)
