from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration loaded from environment variables (12-Factor App design)."""

    app_name: str = "Employee Management System"
    app_env: str = "development"
    database_url: str = "sqlite:///./employees.db"
    secret_key: str = "dev-secret-key-change-me-in-production-min-32-chars"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
