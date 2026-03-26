from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.schemas.user import TokenResponse, UserResponse
from app.services.auth_service import AuthService
from app.services.oauth.kakao import KakaoOAuthClient
from app.services.oauth.apple import AppleOAuthClient
from app.models.user import User

router = APIRouter(prefix="/auth", tags=["Authentication"])


# Kakao OAuth
@router.get("/kakao", summary="Start Kakao OAuth login")
async def kakao_login():
    """
    Redirect to Kakao login page.

    Returns:
        Authorization URL
    """
    client = KakaoOAuthClient()
    auth_url = client.get_authorization_url()
    return {"authorization_url": auth_url}


@router.get("/kakao/callback", response_model=TokenResponse, summary="Kakao OAuth callback")
async def kakao_callback(
    code: str = Query(..., description="Authorization code from Kakao"),
    db: Session = Depends(get_db)
):
    """
    Handle Kakao OAuth callback.

    Args:
        code: Authorization code from Kakao
        db: Database session

    Returns:
        TokenResponse with JWT tokens
    """
    client = KakaoOAuthClient()
    auth_service = AuthService(db)

    # Exchange code for access token
    access_token = await client.get_access_token(code)

    # Get user info from Kakao
    oauth_user_info = await client.get_user_info(access_token)

    # Create/update user and generate JWT tokens
    return auth_service.authenticate_oauth_user(oauth_user_info)


# Apple OAuth
@router.get("/apple", summary="Start Apple OAuth login")
async def apple_login():
    """
    Redirect to Apple login page.

    Returns:
        Authorization URL
    """
    client = AppleOAuthClient()
    auth_url = client.get_authorization_url()
    return {"authorization_url": auth_url}


@router.post("/apple/callback", response_model=TokenResponse, summary="Apple OAuth callback")
async def apple_callback(
    code: str = Query(..., description="Authorization code from Apple"),
    db: Session = Depends(get_db)
):
    """
    Handle Apple OAuth callback (POST method).

    Args:
        code: Authorization code from Apple
        db: Database session

    Returns:
        TokenResponse with JWT tokens
    """
    client = AppleOAuthClient()
    auth_service = AuthService(db)

    # Exchange code for ID token
    id_token = await client.get_access_token(code)

    # Get user info from ID token
    oauth_user_info = await client.get_user_info(id_token)

    # Create/update user and generate JWT tokens
    return auth_service.authenticate_oauth_user(oauth_user_info)


# Common endpoints
@router.get("/me", response_model=UserResponse, summary="Get current user")
async def get_me(current_user: User = Depends(get_current_user)):
    """
    Get current authenticated user information.

    Args:
        current_user: Current user from JWT token

    Returns:
        UserResponse with user information
    """
    return current_user


@router.post("/refresh", response_model=TokenResponse, summary="Refresh access token")
async def refresh_token(
    refresh_token: str,
    db: Session = Depends(get_db)
):
    """
    Refresh access token using refresh token.

    Args:
        refresh_token: Refresh token
        db: Database session

    Returns:
        TokenResponse with new tokens
    """
    from app.core.security import verify_token

    # Verify refresh token
    payload = verify_token(refresh_token, token_type="refresh")
    user_id = payload.get("sub")

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    # Get user
    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    # Generate new tokens
    auth_service = AuthService(db)
    return auth_service.generate_tokens(user)
