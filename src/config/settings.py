from pydantic import Field, validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False, extra="ignore"
    )

    # Cloudflare R2 Configuration
    r2_access_key_id: str = Field(..., description="R2 access key ID")
    r2_secret_access_key: str = Field(..., description="R2 secret access key")
    r2_bucket_name: str = Field(..., description="R2 bucket name")
    r2_endpoint_url: str = Field(..., description="R2 endpoint URL")

    # Application Settings
    log_level: str = Field(default="INFO", description="Logging level")
    environment: str = Field(default="development", description="Environment name")

    # Bluesky Integration
    bluesky_handle: str | None = Field(
        default=None, description="Bluesky handle (e.g., user.bsky.social)"
    )
    bluesky_app_password: str | None = Field(
        default=None, description="Bluesky app password for authentication"
    )

    # Future Integrations
    anthropic_api_key: str | None = Field(default=None, description="Anthropic API key")

    @validator("log_level")
    def validate_log_level(cls, v: str) -> str:
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        v_upper = v.upper()
        if v_upper not in valid_levels:
            raise ValueError(f"Invalid log level: {v}. Must be one of {valid_levels}")
        return v_upper

    @validator("environment")
    def validate_environment(cls, v: str) -> str:
        valid_envs = ["development", "staging", "production"]
        v_lower = v.lower()
        if v_lower not in valid_envs:
            raise ValueError(f"Invalid environment: {v}. Must be one of {valid_envs}")
        return v_lower

    @property
    def is_production(self) -> bool:
        return self.environment == "production"

    @property
    def is_development(self) -> bool:
        return self.environment == "development"

    @property
    def has_bluesky_credentials(self) -> bool:
        """Check if Bluesky credentials are configured."""
        return self.bluesky_handle is not None and self.bluesky_app_password is not None
    
    @property
    def has_anthropic_credentials(self) -> bool:
        """Check if Anthropic API key is configured."""
        return self.anthropic_api_key is not None


def get_settings() -> Settings:
    """Get application settings singleton."""
    return Settings()
