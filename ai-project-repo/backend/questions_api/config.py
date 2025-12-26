"""
Configuration for the Questions API
"""
from pathlib import Path
from typing import Optional

from pydantic_settings import BaseSettings


def get_storage_path() -> str:
    """Get the absolute path to the storage directory"""
    # Get the directory where this config file is located
    current_file = Path(__file__).parent
    # Go up one level to backend/, then to storage/jobs
    storage_path = current_file.parent / "storage" / "jobs"
    return str(storage_path.absolute())


class Settings(BaseSettings):
    """Application settings"""
    
    # API Configuration
    app_name: str = "Interview Questions API"
    app_version: str = "1.0.0"
    debug: bool = False
    
    # Server Configuration
    host: str = "0.0.0.0"
    port: int = 8000
    
    # Storage Configuration - use absolute path
    storage_path: str = get_storage_path()
    
    # Cache Configuration
    enable_cache: bool = True
    cache_ttl: int = 300  # 5 minutes
    
    # CORS Configuration
    cors_origins: list = ["*"]
    cors_methods: list = ["*"]
    cors_headers: list = ["*"]
    
    # Pagination
    default_page_size: int = 10
    max_page_size: int = 100
    
    # Logging
    log_level: str = "INFO"
    
    class Config:
        env_file = ".env"
        env_prefix = "QUESTIONS_API_"

# Global settings instance
settings = Settings()
