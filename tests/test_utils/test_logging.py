import logging
from unittest.mock import Mock, patch

from src.utils.logging import get_logger, setup_logging


class TestGetLogger:
    def teardown_method(self):
        """Clean up loggers after each test."""
        # Clear the cache
        get_logger.cache_clear()

        # Remove handlers from test loggers
        for name in ["test_logger", "test_logger_2"]:
            logger = logging.getLogger(name)
            for handler in logger.handlers[:]:
                logger.removeHandler(handler)

    def test_get_logger_basic(self):
        """Test basic logger creation."""
        logger = get_logger("test_logger")

        assert isinstance(logger, logging.Logger)
        assert logger.name == "test_logger"
        assert len(logger.handlers) > 0
        assert not logger.propagate

    def test_get_logger_with_level(self):
        """Test logger creation with specific level."""
        logger = get_logger("test_logger", level="DEBUG")

        assert logger.level == logging.DEBUG
        assert logger.handlers[0].level == logging.DEBUG

    def test_get_logger_invalid_level_fallback(self):
        """Test logger creation with invalid level falls back to INFO."""
        logger = get_logger("test_logger", level="INVALID")

        # Should fall back to INFO when invalid level is provided
        assert logger.level == logging.INFO

    def test_get_logger_caching(self):
        """Test that get_logger caches logger instances."""
        logger1 = get_logger("test_logger")
        logger2 = get_logger("test_logger")

        assert logger1 is logger2

    def test_get_logger_different_names(self):
        """Test that different names create different loggers."""
        logger1 = get_logger("test_logger_1")
        logger2 = get_logger("test_logger_2")

        assert logger1 is not logger2
        assert logger1.name != logger2.name

    def test_get_logger_no_duplicate_handlers(self):
        """Test that calling get_logger multiple times doesn't add duplicate handlers."""
        logger1 = get_logger("test_logger")
        initial_handler_count = len(logger1.handlers)

        logger2 = get_logger("test_logger")  # Should return cached instance
        final_handler_count = len(logger2.handlers)

        assert initial_handler_count == final_handler_count
        assert logger1 is logger2

    def test_get_logger_handler_configuration(self):
        """Test that logger handler is configured correctly."""
        logger = get_logger("test_logger")

        assert len(logger.handlers) == 1
        handler = logger.handlers[0]

        assert isinstance(handler, logging.StreamHandler)
        assert handler.formatter is not None

        # Check formatter format
        formatter = handler.formatter
        assert "%(asctime)s" in formatter._fmt
        assert "%(name)s" in formatter._fmt
        assert "%(levelname)s" in formatter._fmt
        assert "%(message)s" in formatter._fmt

    @patch("src.utils.logging.get_settings")
    def test_get_logger_uses_settings(self, mock_get_settings):
        """Test that get_logger uses settings for log level."""
        mock_settings = Mock()
        mock_settings.log_level = "WARNING"
        mock_get_settings.return_value = mock_settings

        logger = get_logger("test_logger")

        assert logger.level == logging.WARNING
        mock_get_settings.assert_called_once()

    @patch("src.utils.logging.get_settings")
    def test_get_logger_settings_exception_fallback(self, mock_get_settings):
        """Test fallback when settings can't be loaded."""
        mock_get_settings.side_effect = Exception("Settings error")

        logger = get_logger("test_logger")

        # Should fall back to INFO level
        assert logger.level == logging.INFO

    def test_get_logger_level_override(self):
        """Test that explicit level parameter overrides settings."""
        with patch("src.utils.logging.get_settings") as mock_get_settings:
            mock_settings = Mock()
            mock_settings.log_level = "INFO"
            mock_get_settings.return_value = mock_settings

            logger = get_logger("test_logger", level="ERROR")

            # Explicit level should override settings
            assert logger.level == logging.ERROR
            # Settings should not be called when level is explicitly provided
            mock_get_settings.assert_not_called()


class TestSetupLogging:
    def teardown_method(self):
        """Clean up root logger after each test."""
        root_logger = logging.getLogger()
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)

    def test_setup_logging_basic(self):
        """Test basic logging setup."""
        setup_logging()

        root_logger = logging.getLogger()
        assert root_logger.level == logging.WARNING
        assert len(root_logger.handlers) > 0

    def test_setup_logging_with_level(self):
        """Test logging setup with specific level."""
        setup_logging(level="DEBUG")

        root_logger = logging.getLogger()
        # Root logger should still be WARNING to reduce noise
        assert root_logger.level == logging.WARNING

    def test_setup_logging_handler_configuration(self):
        """Test that setup_logging configures handler correctly."""
        setup_logging()

        root_logger = logging.getLogger()
        assert len(root_logger.handlers) == 1

        handler = root_logger.handlers[0]
        assert isinstance(handler, logging.StreamHandler)
        assert handler.formatter is not None

    def test_setup_logging_removes_existing_handlers(self):
        """Test that setup_logging removes existing handlers."""
        root_logger = logging.getLogger()

        # Add a dummy handler
        dummy_handler = logging.StreamHandler()
        root_logger.addHandler(dummy_handler)

        initial_handler_count = len(root_logger.handlers)
        assert initial_handler_count > 0

        setup_logging()

        # Should have only one handler (the new one)
        assert len(root_logger.handlers) == 1
        assert dummy_handler not in root_logger.handlers

    def test_setup_logging_third_party_loggers(self):
        """Test that third-party loggers are configured to reduce noise."""
        setup_logging()

        # Check that noisy third-party loggers are set to WARNING
        assert logging.getLogger("boto3").level == logging.WARNING
        assert logging.getLogger("botocore").level == logging.WARNING
        assert logging.getLogger("urllib3").level == logging.WARNING

    def test_setup_logging_formatter(self):
        """Test that the formatter is configured correctly."""
        setup_logging()

        root_logger = logging.getLogger()
        handler = root_logger.handlers[0]
        formatter = handler.formatter

        # Check formatter format string
        assert "%(asctime)s" in formatter._fmt
        assert "%(name)s" in formatter._fmt
        assert "%(levelname)s" in formatter._fmt
        assert "%(message)s" in formatter._fmt

        # Check date format
        assert formatter.datefmt == "%Y-%m-%d %H:%M:%S"


class TestLoggingIntegration:
    def teardown_method(self):
        """Clean up after each test."""
        get_logger.cache_clear()

        # Clean up test loggers
        for name in ["integration_test_logger"]:
            logger = logging.getLogger(name)
            for handler in logger.handlers[:]:
                logger.removeHandler(handler)

        # Clean up root logger
        root_logger = logging.getLogger()
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)

    def test_setup_and_get_logger_integration(self):
        """Test integration between setup_logging and get_logger."""
        # First setup logging
        setup_logging()

        # Then get a logger
        logger = get_logger("integration_test_logger")

        # Logger should work correctly
        assert isinstance(logger, logging.Logger)
        assert not logger.propagate
        assert len(logger.handlers) > 0

    @patch("src.utils.logging.get_settings")
    def test_logging_with_settings_integration(self, mock_get_settings):
        """Test complete logging setup with settings."""
        mock_settings = Mock()
        mock_settings.log_level = "DEBUG"
        mock_get_settings.return_value = mock_settings

        # Setup logging first
        setup_logging()

        # Get logger (should use settings)
        logger = get_logger("integration_test_logger")

        assert logger.level == logging.DEBUG
        mock_get_settings.assert_called_once()
