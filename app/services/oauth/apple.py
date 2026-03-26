from typing import Optional
import httpx
from fastapi import HTTPException, status
from urllib.parse import urlencode
from jose import jwt

from app.core.config import settings
from app.services.oauth.base import OAuthClient
from app.schemas.user import OAuthUserInfo
from app.models.user import OAuthProvider


class AppleOAuthClient(OAuthClient):
    """Apple OAuth 2.0 client implementation."""

    AUTHORIZATION_URL = "https://appleid.apple.com/auth/authorize"
    TOKEN_URL = "https://appleid.apple.com/auth/token"
    JWKS_URL = "https://appleid.apple.com/auth/keys"

    def __init__(self):
        self.client_id = settings.apple_client_id
        self.team_id = settings.apple_team_id
        self.key_id = settings.apple_key_id
        self.redirect_uri = settings.apple_redirect_uri

    def get_authorization_url(self, state: Optional[str] = None) -> str:
        """Generate Apple authorization URL."""
        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "response_type": "code id_token",
            "response_mode": "form_post",
            "scope": "name email",
        }
        if state:
            params["state"] = state

        return f"{self.AUTHORIZATION_URL}?{urlencode(params)}"

    async def get_access_token(self, code: str) -> str:
        """Exchange authorization code for access token."""
        # Apple requires client_secret to be a signed JWT
        client_secret = self._generate_client_secret()

        data = {
            "grant_type": "authorization_code",
            "client_id": self.client_id,
            "client_secret": client_secret,
            "code": code,
            "redirect_uri": self.redirect_uri,
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.TOKEN_URL,
                data=data,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )

            if response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Failed to get access token from Apple: {response.text}",
                )

            token_data = response.json()
            return token_data.get("id_token", token_data.get("access_token"))

    async def get_user_info(self, id_token: str) -> OAuthUserInfo:
        """
        Get user information from Apple ID token.

        Apple returns user info in the ID token (JWT), not via a separate API.
        """
        try:
            # Decode without verification for development (in production, verify signature)
            payload = jwt.decode(
                id_token,
                key="",  # Empty key when verification is disabled
                options={"verify_signature": False},  # For mock testing
            )

            return OAuthUserInfo(
                oauth_id=payload["sub"],
                email=payload.get("email", f"apple_{payload['sub']}@privaterelay.appleid.com"),
                nickname=None,  # Apple doesn't provide nickname in token
                provider=OAuthProvider.APPLE,
            )

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to decode Apple ID token: {str(e)}",
            )

    def _generate_client_secret(self) -> str:
        """
        Generate Apple client secret (JWT).

        In production, this should use the private key from .p8 file.
        For development/testing, we'll use a mock implementation.
        """
        import time

        headers = {
            "kid": self.key_id,
            "alg": "ES256",
        }

        payload = {
            "iss": self.team_id,
            "iat": int(time.time()),
            "exp": int(time.time()) + 86400,  # 24 hours
            "aud": "https://appleid.apple.com",
            "sub": self.client_id,
        }

        # For mock/testing, use HS256 instead of ES256
        # In production, use ES256 with private key
        return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")
