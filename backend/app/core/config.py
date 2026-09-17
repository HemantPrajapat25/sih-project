import os
from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(case_sensitive=True, env_file=".env", extra="allow")

    APP_NAME: str = "NumberGuard"
    APP_ENV: str = "development"
    APP_DEBUG: bool = True
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = "numberguard_super_secret_jwt_key_32_bytes_long_change_in_prod!"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480
    ALGORITHM: str = "HS256"

    # Privacy Pepper for HMAC-SHA256 phone number indexing
    PHONE_HASH_PEPPER: str = "numberguard_secure_phone_hmac_pepper_key_2026"

    # Database
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "sqlite+aiosqlite:///./numberguard.db"
    )
    SYNC_DATABASE_URL: str = os.getenv(
        "SYNC_DATABASE_URL",
        "sqlite:///./numberguard.db"
    )

    # Redis & Queue
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    CELERY_BROKER_URL: str = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")

    # Cooling defaults (days)
    DEFAULT_COOLING_DAYS_STANDARD: int = 60
    DEFAULT_COOLING_DAYS_BANKING: int = 90
    DEFAULT_COOLING_DAYS_HIGH_RISK: int = 120

    # Risk Engine Thresholds
    RISK_THRESHOLD_LOW: int = 25
    RISK_THRESHOLD_MEDIUM: int = 55
    RISK_THRESHOLD_HIGH: int = 79

    # Mock Services
    MOCK_EXTERNAL_SERVICES: bool = True
    SANDBOX_WEBHOOK_LATENCY_MS: int = 200

    # Adapter & Integration Providers (Phase 3)
    PHONE_LOOKUP_PROVIDER: str = "mock"   # "mock" | "twilio"
    TWILIO_ACCOUNT_SID: str = ""
    TWILIO_AUTH_TOKEN: str = ""
    EMAIL_PROVIDER: str = "mock"          # "mock" | "smtp" | "sendgrid"
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASS: str = ""
    WEBHOOK_HMAC_SECRET: str = "numberguard_webhook_hmac_secret"

    # CORS
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:8000",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8000",
        "*"
    ]

settings = Settings()
