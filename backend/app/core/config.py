"""Application settings and environment configuration."""

import os
from typing import List, Literal
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # App Information
    PROJECT_NAME: str = "ColdChain Sentinel"
    VERSION: str = "1.0.0"
    API_V1_PREFIX: str = "/api"
    APP_ENV: Literal["development", "staging", "production"] = "development"
    APP_DEBUG: bool = True
    APP_SECRET_KEY: str = Field(
        default="coldchain-sentinel-insecure-dev-key-change-in-production-123456",
        description="Cryptographic secret key for signing tokens"
    )
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    TRUSTED_PROXY_CIDRS: List[str] = ["127.0.0.1/32", "::1/128"]

    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://coldchain-sentinel.vercel.app",
        "https://coldchain-sentinel-omega.vercel.app",
        "https://coldchain-sentinel-paradox-d082.vercel.app",
    ]

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v):
        defaults = [
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "https://coldchain-sentinel.vercel.app",
            "https://coldchain-sentinel-omega.vercel.app",
            "https://coldchain-sentinel-paradox-d082.vercel.app",
        ]
        if isinstance(v, str) and not v.startswith("["):
            parsed = [i.strip() for i in v.split(",") if i.strip()]
            return list(dict.fromkeys(parsed + defaults))
        elif isinstance(v, list):
            return list(dict.fromkeys(v + defaults))
        elif isinstance(v, str):
            return v
        raise ValueError(v)

    # Persistence
    DATABASE_URL: str = "sqlite:///./coldchain.db"

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def assemble_database_url(cls, v: str) -> str:
        if isinstance(v, str):
            if v.startswith("postgres://"):
                return v.replace("postgres://", "postgresql+psycopg2://", 1)
            elif v.startswith("postgresql://") and not v.startswith("postgresql+"):
                return v.replace("postgresql://", "postgresql+psycopg2://", 1)
        return v

    # Evidence File Storage
    STORAGE_BACKEND: Literal["local", "s3", "supabase"] = "local"
    STORAGE_LOCAL_PATH: str = "backend/storage"

    # Supabase Storage Settings
    SUPABASE_URL: str = ""
    SUPABASE_KEY: str = ""
    SUPABASE_STORAGE_BUCKET: str = "evidence"

    # S3 / Cloud Storage Settings
    S3_BUCKET_NAME: str = "coldchain-sentinel-evidence"
    S3_REGION: str = "us-east-1"
    S3_ACCESS_KEY_ID: str = ""
    S3_SECRET_ACCESS_KEY: str = ""
    S3_ENDPOINT_URL: str = ""

    # PayPal REST API Configuration
    PAYPAL_MODE: Literal["SANDBOX", "DEMO"] = "SANDBOX"
    PAYPAL_BASE_URL: str = "https://api-m.sandbox.paypal.com"
    PAYPAL_CLIENT_ID: str = ""
    PAYPAL_CLIENT_SECRET: str = ""
    PAYPAL_WEBHOOK_ID: str = ""

    # AI Integration (Google Gemini)
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.5-flash"

    # Google OAuth 2.0 Integration
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GOOGLE_REDIRECT_URI: str = ""
    FRONTEND_URL: str = "http://localhost:3000"

    @property
    def resolved_google_redirect_uri(self) -> str:
        """Resolve OAuth redirect URI based on environment or explicit override.
        
        - If GOOGLE_REDIRECT_URI is provided, strictly honor it.
        - In production (APP_ENV == 'production'), use deployed Render domain.
        - In local development, use localhost.
        """
        if self.GOOGLE_REDIRECT_URI:
            return self.GOOGLE_REDIRECT_URI
        if self.APP_ENV == "production":
            return "https://coldchain-sentinel-7ax3.onrender.com/api/auth/google/callback"
        return "http://localhost:8000/api/auth/google/callback"

    @property
    def resolved_frontend_url(self) -> str:
        """Resolve Frontend URL for OAuth redirects."""
        if self.FRONTEND_URL and self.FRONTEND_URL != "http://localhost:3000":
            return self.FRONTEND_URL
        if self.APP_ENV == "production":
            return "https://coldchain-sentinel.vercel.app"
        return "http://localhost:3000"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )


settings = Settings()
