from abc import ABC, abstractmethod
from typing import Optional

from app.schemas.user import OAuthUserInfo


class OAuthClient(ABC):
    """Abstract base class for OAuth clients."""

    @abstractmethod
    def get_authorization_url(self, state: Optional[str] = None) -> str:
        """
        Get the authorization URL to redirect the user.

        Args:
            state: Optional state parameter for CSRF protection

        Returns:
            Authorization URL string
        """
        pass

    @abstractmethod
    async def get_access_token(self, code: str) -> str:
        """
        Exchange authorization code for access token.

        Args:
            code: Authorization code from OAuth provider

        Returns:
            Access token string

        Raises:
            HTTPException: If token exchange fails
        """
        pass

    @abstractmethod
    async def get_user_info(self, access_token: str) -> OAuthUserInfo:
        """
        Get user information from OAuth provider.

        Args:
            access_token: Access token from provider

        Returns:
            OAuthUserInfo object with user data

        Raises:
            HTTPException: If user info retrieval fails
        """
        pass
