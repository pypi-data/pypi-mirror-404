"""Pytest configuration and fixtures."""

import pytest
from unittest.mock import MagicMock, patch

@pytest.fixture
def mock_client():
    """Create a mock Dremio client."""
    client = MagicMock()
    return client

@pytest.fixture
def mock_profile_manager():
    """Mock ProfileManager."""
    with patch("dremio_cli.config.ProfileManager") as mock_config, \
         patch("dremio_cli.cli.ProfileManager", new=mock_config), \
         patch("dremio_cli.commands.reflection.ProfileManager", new=mock_config), \
         patch("dremio_cli.commands.script.ProfileManager", new=mock_config):
         
        instance = mock_config.return_value
        instance.get_profile.return_value = {
            "name": "test",
            "base_url": "http://localhost",
            "token": "secret"
        }
        instance.get_default_profile.return_value = "test"
        yield mock_config
