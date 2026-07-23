"""
Configuration management using Pydantic and environment variables
"""

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Telegram MTProto credentials
    api_id: int
    api_hash: str
    session_string: str
    
    # Application configuration
    jwt_secret: str
    database_url: str = "sqlite+aiosqlite:///./streaming_platform.db"
    
    # Telegram channel configuration
    telegram_channel_id: int
    
    # Server configuration
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False
    
    # Streaming configuration
    chunk_size: int = 1024 * 1024  # 1MB chunks for streaming
    max_concurrent_streams: int = 10
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()


# Export settings instance
settings = get_settings()
