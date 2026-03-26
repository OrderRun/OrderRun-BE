from typing import Optional
import httpx
from fastapi import HTTPException, status
from urllib.parse import urlencode

from app.core.config import settings
from app.services.oauth.base import OAuthClient
from app.schemas.user import OAuthUserInfo
from app.models.user import OAuthProvider


class KakaoOAuthClient(OAuthClient):
    """Kakao OAuth 2.0 client implementation."""

    AUTHORIZATION_URL = "https://kauth.kakao.com/oauth/authorize"
    TOKEN_URL = "https://kauth.kakao.com/oauth/token"
    USER_INFO_URL = "https://kapi.kakao.com/v2/user/me"

    def __init__(self):
        self.client_id = settings.kakao_client_id
        self.client_secret = settings.kakao_client_secret
        self.redirect_uri = settings.kakao_redirect_uri

    def get_authorization_url(self, state: Optional[str] = None) -> str:
        """Generate Kakao authorization URL."""
        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "response_type": "code",
        }
        if state:
            params["state"] = state

        return f"{self.AUTHORIZATION_URL}?{urlencode(params)}"

    async def get_access_token(self, code: str) -> str:
        """Exchange authorization code for access token."""
        data = {
            "grant_type": "authorization_code",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "redirect_uri": self.redirect_uri,
            "code": code,
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
                    detail=f"Failed to get access token from Kakao: {response.text}",
                )

            token_data = response.json()
            return token_data["access_token"]

    async def get_user_info(self, access_token: str) -> OAuthUserInfo:
        """Get user information from Kakao."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                self.USER_INFO_URL,
                headers={"Authorization": f"Bearer {access_token}"},
            )

            if response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Failed to get user info from Kakao: {response.text}",
                )

            user_data = response.json()

            # Extract user information from Kakao response
            kakao_account = user_data.get("kakao_account", {})
            profile = kakao_account.get("profile", {})

            return OAuthUserInfo(
                oauth_id=str(user_data["id"]),
                email=kakao_account.get("email", f"kakao_{user_data['id']}@temp.com"),
                nickname=profile.get("nickname"),
                provider=OAuthProvider.KAKAO,
            )
