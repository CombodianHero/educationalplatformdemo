"""
Configuration via environment variables (.env)
"""
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    api_id: int
    api_hash: str
    session_string: str = ""
    jwt_secret: str
    telegram_channel_id: int
    database_url: str = "sqlite+aiosqlite:///./streaming_platform.db"
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False
    chunk_size: int = 1024 * 1024  # 1MB
    max_concurrent_streams: int = 10

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()
