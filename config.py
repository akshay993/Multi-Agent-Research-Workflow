from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    database_url: str
    anthropic_api_key: str
    tavily_api_key: str
    model: str = "anthropic:claude-sonnet-4-5-20250929"

    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "allow"  # Allow extra env vars without error


settings = Settings()
