from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    # Application
    app_env: str = "development"
    app_debug: bool = True
    secret_key: str

    # Database
    db_host: str = "localhost"
    db_port: int = 3306
    db_username: str
    db_password: str
    db_name: str

    # JWT
    jwt_secret: str
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 60
    jwt_refresh_token_expire_days: int = 30

    # OAuth - Kakao
    kakao_client_id: str
    kakao_client_secret: str
    kakao_redirect_uri: str

    # OAuth - Apple
    apple_client_id: str
    apple_team_id: str
    apple_key_id: str
    apple_private_key_path: str
    apple_redirect_uri: str

    # FCM (Firebase Cloud Messaging)
    fcm_credentials_path: Optional[str] = None

    # Server
    server_host: str = "0.0.0.0"
    server_port: int = 8000

    @property
    def database_url(self) -> str:
        """Construct database URL for SQLAlchemy."""
        return (
            f"mysql+pymysql://{self.db_username}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
            f"?charset=utf8mb4"
        )

    @property
    def database_url_sync(self) -> str:
        """Synchronous database URL for Alembic."""
        return self.database_url


# Global settings instance
settings = Settings()
