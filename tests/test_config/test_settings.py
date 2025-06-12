import os
from unittest.mock import patch

import pytest
from pydantic import ValidationError

from src.config.settings import Settings, get_settings


class TestSettings:
    def test_settings_with_all_required_fields(self):
        """Test settings creation with all required fields."""
        settings = Settings(
            r2_access_key_id="test_key",
            r2_secret_access_key="test_secret",
            r2_bucket_name="test-bucket",
            r2_endpoint_url="https://test.r2.cloudflarestorage.com",
        )

        assert settings.r2_access_key_id == "test_key"
        assert settings.r2_secret_access_key == "test_secret"
        assert settings.r2_bucket_name == "test-bucket"
        assert settings.r2_endpoint_url == "https://test.r2.cloudflarestorage.com"

        # Check defaults
        assert settings.log_level == "INFO"
        assert settings.environment == "development"
        assert settings.bluesky_handle is None
        assert settings.bluesky_app_password is None
        assert settings.anthropic_api_key is None

    def test_settings_missing_required_fields(self):
        """Test that missing required fields raise ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            Settings()

        error_msg = str(exc_info.value)
        assert "r2_access_key_id" in error_msg
        assert "r2_secret_access_key" in error_msg
        assert "r2_bucket_name" in error_msg
        assert "r2_endpoint_url" in error_msg

    def test_settings_with_optional_fields(self):
        """Test settings with optional fields set."""
        settings = Settings(
            r2_access_key_id="test_key",
            r2_secret_access_key="test_secret",
            r2_bucket_name="test-bucket",
            r2_endpoint_url="https://test.r2.cloudflarestorage.com",
            log_level="DEBUG",
            environment="production",
            bluesky_handle="user.bsky.social",
            bluesky_app_password="app_pass",
            anthropic_api_key="anthropic_key",
        )

        assert settings.log_level == "DEBUG"
        assert settings.environment == "production"
        assert settings.bluesky_handle == "user.bsky.social"
        assert settings.bluesky_app_password == "app_pass"
        assert settings.anthropic_api_key == "anthropic_key"

    def test_log_level_validation(self):
        """Test log level validation."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]

        for level in valid_levels:
            settings = Settings(
                r2_access_key_id="key",
                r2_secret_access_key="secret",
                r2_bucket_name="bucket",
                r2_endpoint_url="https://test.com",
                log_level=level,
            )
            assert settings.log_level == level

        # Test case insensitive
        settings = Settings(
            r2_access_key_id="key",
            r2_secret_access_key="secret",
            r2_bucket_name="bucket",
            r2_endpoint_url="https://test.com",
            log_level="debug",
        )
        assert settings.log_level == "DEBUG"

        # Test invalid level
        with pytest.raises(ValidationError) as exc_info:
            Settings(
                r2_access_key_id="key",
                r2_secret_access_key="secret",
                r2_bucket_name="bucket",
                r2_endpoint_url="https://test.com",
                log_level="INVALID",
            )
        assert "Invalid log level" in str(exc_info.value)

    def test_environment_validation(self):
        """Test environment validation."""
        valid_envs = ["development", "staging", "production"]

        for env in valid_envs:
            settings = Settings(
                r2_access_key_id="key",
                r2_secret_access_key="secret",
                r2_bucket_name="bucket",
                r2_endpoint_url="https://test.com",
                environment=env,
            )
            assert settings.environment == env

        # Test case insensitive
        settings = Settings(
            r2_access_key_id="key",
            r2_secret_access_key="secret",
            r2_bucket_name="bucket",
            r2_endpoint_url="https://test.com",
            environment="PRODUCTION",
        )
        assert settings.environment == "production"

        # Test invalid environment
        with pytest.raises(ValidationError) as exc_info:
            Settings(
                r2_access_key_id="key",
                r2_secret_access_key="secret",
                r2_bucket_name="bucket",
                r2_endpoint_url="https://test.com",
                environment="invalid",
            )
        assert "Invalid environment" in str(exc_info.value)

    def test_environment_properties(self):
        """Test environment helper properties."""
        dev_settings = Settings(
            r2_access_key_id="key",
            r2_secret_access_key="secret",
            r2_bucket_name="bucket",
            r2_endpoint_url="https://test.com",
            environment="development",
        )
        assert dev_settings.is_development is True
        assert dev_settings.is_production is False

        prod_settings = Settings(
            r2_access_key_id="key",
            r2_secret_access_key="secret",
            r2_bucket_name="bucket",
            r2_endpoint_url="https://test.com",
            environment="production",
        )
        assert prod_settings.is_development is False
        assert prod_settings.is_production is True

        staging_settings = Settings(
            r2_access_key_id="key",
            r2_secret_access_key="secret",
            r2_bucket_name="bucket",
            r2_endpoint_url="https://test.com",
            environment="staging",
        )
        assert staging_settings.is_development is False
        assert staging_settings.is_production is False


class TestSettingsEnvironmentLoading:
    def test_settings_from_env_vars(self):
        """Test loading settings from environment variables."""
        env_vars = {
            "R2_ACCESS_KEY_ID": "env_key",
            "R2_SECRET_ACCESS_KEY": "env_secret",
            "R2_BUCKET_NAME": "env-bucket",
            "R2_ENDPOINT_URL": "https://env.r2.cloudflarestorage.com",
            "LOG_LEVEL": "ERROR",
            "ENVIRONMENT": "staging",
            "BLUESKY_HANDLE": "env.bsky.social",
            "ANTHROPIC_API_KEY": "env_anthropic_key",
        }

        with patch.dict(os.environ, env_vars, clear=True):
            settings = Settings()

            assert settings.r2_access_key_id == "env_key"
            assert settings.r2_secret_access_key == "env_secret"
            assert settings.r2_bucket_name == "env-bucket"
            assert settings.r2_endpoint_url == "https://env.r2.cloudflarestorage.com"
            assert settings.log_level == "ERROR"
            assert settings.environment == "staging"
            assert settings.bluesky_handle == "env.bsky.social"
            assert settings.anthropic_api_key == "env_anthropic_key"

    def test_settings_case_insensitive_env_vars(self):
        """Test that environment variables are case insensitive."""
        env_vars = {
            "r2_access_key_id": "lower_key",
            "R2_SECRET_ACCESS_KEY": "upper_secret",
            "r2_bucket_name": "lower-bucket",
            "R2_ENDPOINT_URL": "https://test.com",
        }

        with patch.dict(os.environ, env_vars, clear=True):
            settings = Settings()

            assert settings.r2_access_key_id == "lower_key"
            assert settings.r2_secret_access_key == "upper_secret"
            assert settings.r2_bucket_name == "lower-bucket"

    def test_explicit_values_override_env(self):
        """Test that explicit values override environment variables."""
        env_vars = {
            "R2_ACCESS_KEY_ID": "env_key",
            "R2_SECRET_ACCESS_KEY": "env_secret",
            "R2_BUCKET_NAME": "env-bucket",
            "R2_ENDPOINT_URL": "https://env.com",
            "LOG_LEVEL": "ERROR",
        }

        with patch.dict(os.environ, env_vars, clear=True):
            settings = Settings(r2_access_key_id="explicit_key", log_level="DEBUG")

            # Explicit values should override env
            assert settings.r2_access_key_id == "explicit_key"
            assert settings.log_level == "DEBUG"

            # Non-overridden values should come from env
            assert settings.r2_secret_access_key == "env_secret"
            assert settings.r2_bucket_name == "env-bucket"


class TestGetSettings:
    def test_get_settings_function(self):
        """Test get_settings function."""
        with patch.dict(
            os.environ,
            {
                "R2_ACCESS_KEY_ID": "func_key",
                "R2_SECRET_ACCESS_KEY": "func_secret",
                "R2_BUCKET_NAME": "func-bucket",
                "R2_ENDPOINT_URL": "https://func.com",
            },
            clear=True,
        ):
            settings = get_settings()

            assert isinstance(settings, Settings)
            assert settings.r2_access_key_id == "func_key"

    def test_get_settings_returns_new_instance(self):
        """Test that get_settings returns new instances."""
        with patch.dict(
            os.environ,
            {
                "R2_ACCESS_KEY_ID": "key",
                "R2_SECRET_ACCESS_KEY": "secret",
                "R2_BUCKET_NAME": "bucket",
                "R2_ENDPOINT_URL": "https://test.com",
            },
            clear=True,
        ):
            settings1 = get_settings()
            settings2 = get_settings()

            # Should be different instances but with same values
            assert settings1 is not settings2
            assert settings1.r2_access_key_id == settings2.r2_access_key_id
