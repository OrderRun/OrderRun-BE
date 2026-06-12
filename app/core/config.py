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

    # Logging
    log_level: str = "INFO"
    log_dir: str = "/app/logs"
    log_file_enabled: bool = False
    log_retention_days: int = 14

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
    jwt_refresh_token_expire_days: int = 7

    # FCM (Firebase Cloud Messaging)
    fcm_credentials_path: Optional[str] = None   # 로컬 개발: 파일 경로
    fcm_credentials_json: Optional[str] = None   # 배포 환경: JSON 문자열 (GitHub Secret)

    # AWS SNS (SMS)
    aws_sns_region: str = "ap-northeast-2"
    aws_sns_access_key_id: str
    aws_sns_secret_access_key: str
    aws_sns_sms_sender_id: str
    aws_sns_sms_type: str = "Transactional"

    # Server
    server_host: str = "0.0.0.0"
    server_port: int = 8000

    # Payment
    payment_bank_name: str = "국민은행"
    payment_account_number: str = "123-456-789012"
    payment_account_holder: str = "주식회사 오더런"

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
