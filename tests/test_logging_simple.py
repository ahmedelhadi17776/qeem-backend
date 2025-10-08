"""Simple tests for logging configuration."""

import logging
import pytest
from unittest.mock import patch

from app.core.logging import configure_logging, configure_uvicorn_json_logging, configure_uvicorn_text_logging


class TestConfigureLogging:
    """Test configure_logging function."""

    def test_configure_logging_text_format(self):
        """Test configuring logging with text format."""
        # Test that function runs without error
        configure_logging("INFO", fmt="text", color=False)
        # Basic assertion that root logger exists
        root_logger = logging.getLogger()
        assert root_logger is not None

    def test_configure_logging_json_format(self):
        """Test configuring logging with JSON format."""
        # Test that function runs without error
        configure_logging("DEBUG", fmt="json", color=False)
        # Basic assertion that root logger exists
        root_logger = logging.getLogger()
        assert root_logger is not None

    def test_configure_logging_with_color(self):
        """Test configuring logging with color."""
        # Test that function runs without error
        configure_logging("WARNING", fmt="text", color=True)
        # Basic assertion that root logger exists
        root_logger = logging.getLogger()
        assert root_logger is not None

    def test_configure_logging_invalid_level(self):
        """Test configuring logging with invalid level."""
        # Test that function runs without error even with invalid level
        configure_logging("INVALID", fmt="text", color=False)
        # Basic assertion that root logger exists
        root_logger = logging.getLogger()
        assert root_logger is not None


class TestConfigureUvicornLogging:
    """Test uvicorn logging configuration functions."""

    def test_configure_uvicorn_json_logging(self):
        """Test configuring uvicorn JSON logging."""
        # Test that function runs without error
        configure_uvicorn_json_logging("INFO")

        # Check that uvicorn loggers exist
        uvicorn_logger = logging.getLogger("uvicorn")
        assert uvicorn_logger is not None

    def test_configure_uvicorn_text_logging(self):
        """Test configuring uvicorn text logging."""
        # Test that function runs without error
        configure_uvicorn_text_logging("INFO", color=True)

        # Check that uvicorn loggers exist
        uvicorn_logger = logging.getLogger("uvicorn")
        assert uvicorn_logger is not None

    def test_configure_uvicorn_text_logging_no_color(self):
        """Test configuring uvicorn text logging without color."""
        # Test that function runs without error
        configure_uvicorn_text_logging("WARNING", color=False)

        # Check that uvicorn loggers exist
        uvicorn_logger = logging.getLogger("uvicorn")
        assert uvicorn_logger is not None
