"""
AI CodeScan Configuration Example

Copy this file to config.py and update with your actual values.
"""

import os
from pathlib import Path
from typing import Optional

class Config:
    """Base configuration class."""
    
    # Application Settings
    APP_NAME: str = "AI CodeScan"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    
    # OpenAI Configuration
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4")
    OPENAI_MAX_TOKENS: int = int(os.getenv("OPENAI_MAX_TOKENS", "4000"))
    OPENAI_TEMPERATURE: float = float(os.getenv("OPENAI_TEMPERATURE", "0.1"))
    
    # Neo4j Configuration
    NEO4J_URI: str = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    NEO4J_USER: str = os.getenv("NEO4J_USER", "neo4j")
    NEO4J_PASSWORD: str = os.getenv("NEO4J_PASSWORD", "password")
    NEO4J_DATABASE: str = os.getenv("NEO4J_DATABASE", "ai-codescan")
    
    # Redis Configuration
    REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_DB: int = int(os.getenv("REDIS_DB", "0"))
    REDIS_PASSWORD: Optional[str] = os.getenv("REDIS_PASSWORD")
    
    # Streamlit Configuration
    STREAMLIT_SERVER_PORT: int = int(os.getenv("STREAMLIT_SERVER_PORT", "8501"))
    STREAMLIT_SERVER_ADDRESS: str = os.getenv("STREAMLIT_SERVER_ADDRESS", "0.0.0.0")
    
    # Security Configuration
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-here")
    SESSION_TIMEOUT: int = int(os.getenv("SESSION_TIMEOUT", "3600"))
    PAT_ENCRYPTION_KEY: str = os.getenv("PAT_ENCRYPTION_KEY", "your-encryption-key-here")
    
    # Performance Configuration
    MAX_CONCURRENT_TASKS: int = int(os.getenv("MAX_CONCURRENT_TASKS", "5"))
    MAX_REPOSITORY_SIZE_MB: int = int(os.getenv("MAX_REPOSITORY_SIZE_MB", "500"))
    CLONE_TIMEOUT_SECONDS: int = int(os.getenv("CLONE_TIMEOUT_SECONDS", "300"))
    ANALYSIS_TIMEOUT_SECONDS: int = int(os.getenv("ANALYSIS_TIMEOUT_SECONDS", "1800"))
    
    # External Services
    GITHUB_API_BASE_URL: str = os.getenv("GITHUB_API_BASE_URL", "https://api.github.com")
    GITLAB_API_BASE_URL: str = os.getenv("GITLAB_API_BASE_URL", "https://gitlab.com/api/v4")
    BITBUCKET_API_BASE_URL: str = os.getenv("BITBUCKET_API_BASE_URL", "https://api.bitbucket.org/2.0")
    
    # Storage Configuration
    TEMP_REPOS_PATH: Path = Path(os.getenv("TEMP_REPOS_PATH", "./temp_repos"))
    CLEANUP_TEMP_FILES: bool = os.getenv("CLEANUP_TEMP_FILES", "true").lower() == "true"
    TEMP_FILE_TTL_HOURS: int = int(os.getenv("TEMP_FILE_TTL_HOURS", "24"))
    
    # Monitoring & Logging
    ENABLE_PERFORMANCE_MONITORING: bool = os.getenv("ENABLE_PERFORMANCE_MONITORING", "true").lower() == "true"
    LOG_FORMAT: str = os.getenv("LOG_FORMAT", "json")
    LOG_FILE_PATH: str = os.getenv("LOG_FILE_PATH", "logs/ai-codescan.log")
    METRICS_ENABLED: bool = os.getenv("METRICS_ENABLED", "true").lower() == "true"


class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    LOG_LEVEL = "DEBUG"


class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    LOG_LEVEL = "INFO"


class TestingConfig(Config):
    """Testing configuration."""
    DEBUG = True
    LOG_LEVEL = "DEBUG"
    # Use in-memory databases for testing
    NEO4J_URI = "bolt://localhost:7688"  # Test instance
    REDIS_DB = 1  # Test database


# Configuration mapping
config_map = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}

def get_config(config_name: Optional[str] = None) -> Config:
    """Get configuration based on environment."""
    if config_name is None:
        config_name = os.getenv('AI_CODESCAN_ENV', 'default')
    
    return config_map.get(config_name, DevelopmentConfig)() 