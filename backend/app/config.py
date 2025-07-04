"""
Configuration management for SIPCall backend
"""

from pydantic_settings import BaseSettings
from typing import List
import os

class Settings(BaseSettings):
    """Application settings"""
    
    # Environment
    ENVIRONMENT: str = "development"
    DEBUG_MODE: bool = True
    
    # API Configuration
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_SECRET_KEY: str = "your-secret-key-change-in-production"
    
    # Database
    DATABASE_URL: str = "postgresql://sipcall_user:sipcall_password@localhost:5432/sipcall_db"
    DATABASE_ENCRYPTION_KEY: str = "your-32-character-encryption-key"
    
    # JWT Authentication
    JWT_SECRET_KEY: str = "your-jwt-secret-key"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRY_MINUTES: int = 15
    JWT_REFRESH_EXPIRY_DAYS: int = 30
    
    # FreeSWITCH
    FREESWITCH_HOST: str = "localhost"
    FREESWITCH_PORT: int = 8021
    FREESWITCH_PASSWORD: str = "ClueCon"
    FREESWITCH_ESL_HOST: str = "localhost"
    FREESWITCH_ESL_PORT: int = 8021
    
    # SIP Provider
    SIP_PROVIDER_NAME: str = "telnyx"
    SIP_PROVIDER_API_KEY: str = ""
    SIP_PROVIDER_API_SECRET: str = ""
    SIP_PROVIDER_BASE_URL: str = "https://api.telnyx.com/v2"
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_PASSWORD: str = ""
    
    # Security
    CORS_ORIGINS: List[str] = ["http://localhost:3000"]
    ALLOWED_HOSTS: List[str] = ["localhost", "127.0.0.1"]
    RATE_LIMIT_CALLS_PER_MINUTE: int = 10
    RATE_LIMIT_API_PER_MINUTE: int = 100
    
    # Nextcloud Integration
    NEXTCLOUD_BASE_URL: str = ""
    NEXTCLOUD_CLIENT_ID: str = ""
    NEXTCLOUD_CLIENT_SECRET: str = ""
    NEXTCLOUD_REDIRECT_URI: str = ""
    
    # Monitoring
    LOG_LEVEL: str = "INFO"
    PROMETHEUS_ENABLED: bool = False
    PROMETHEUS_PORT: int = 9090
    
    # Email
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM_EMAIL: str = ""
    
    class Config:
        env_file = ".env"
        case_sensitive = True

# Create settings instance
settings = Settings()

# Validate critical settings
if settings.ENVIRONMENT == "production":
    assert settings.API_SECRET_KEY != "your-secret-key-change-in-production", "Change API_SECRET_KEY in production"
    assert settings.JWT_SECRET_KEY != "your-jwt-secret-key", "Change JWT_SECRET_KEY in production"
    assert settings.DATABASE_ENCRYPTION_KEY != "your-32-character-encryption-key", "Change DATABASE_ENCRYPTION_KEY in production"