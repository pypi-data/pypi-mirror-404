"""Tests for script commands."""

import json
from unittest.mock import MagicMock, patch
from click.testing import CliRunner
from dremio_cli.cli import cli


def test_list_scripts(mock_profile_manager, mock_client):
    """Test listing scripts."""
    mock_client.list_scripts.return_value = {"data": [{"id": "123", "name": "script1"}]}
    
    runner = CliRunner()
    with patch("dremio_cli.commands.script.create_client", return_value=mock_client):
        result = runner.invoke(cli, ["script", "list"])
        
    assert result.exit_code == 0
    assert "script1" in result.output
    mock_client.list_scripts.assert_called_with(limit=25, offset=0)


def test_get_script(mock_profile_manager, mock_client):
    """Test getting a script."""
    mock_client.get_script.return_value = {"id": "123", "name": "script1", "content": "SELECT 1"}
    
    runner = CliRunner()
    with patch("dremio_cli.commands.script.create_client", return_value=mock_client):
        result = runner.invoke(cli, ["script", "get", "123"])
        
    assert result.exit_code == 0
    assert "script1" in result.output
    assert "SELECT 1" in result.output
    mock_client.get_script.assert_called_with("123")


def test_create_script(mock_profile_manager, mock_client):
    """Test creating a script."""
    mock_client.create_script.return_value = {"id": "123", "name": "new_script"}
    
    runner = CliRunner()
    
    with patch("dremio_cli.commands.script.create_client", return_value=mock_client):
        result = runner.invoke(cli, ["script", "create", "--name", "new_script", "--content", "SELECT 1"])
        
    assert result.exit_code == 0
    assert "created successfully" in result.output
    assert "123" in result.output
    mock_client.create_script.assert_called_with("new_script", "SELECT 1", None)


def test_update_script(mock_profile_manager, mock_client):
    """Test updating a script."""
    mock_client.update_script.return_value = {"id": "123", "name": "updated_script"}
    
    runner = CliRunner()
    
    with patch("dremio_cli.commands.script.create_client", return_value=mock_client):
        result = runner.invoke(cli, ["script", "update", "123", "--name", "updated_script", "--content", "SELECT 2"])
        
    assert result.exit_code == 0
    assert "updated successfully" in result.output
    mock_client.update_script.assert_called_with("123", "updated_script", "SELECT 2", None)


def test_delete_script(mock_profile_manager, mock_client):
    """Test deleting a script."""
    runner = CliRunner()
    with patch("dremio_cli.commands.script.create_client", return_value=mock_client):
        result = runner.invoke(cli, ["script", "delete", "123", "--yes"])
        
    assert result.exit_code == 0
    assert "deleted successfully" in result.output
    mock_client.delete_script.assert_called_with("123")


def test_script_not_supported(mock_profile_manager):
    """Test graceful handling when scripts are not supported (e.g. Software client)."""
    # Create a mock client that DOES NOT have script methods
    mock_client_no_scripts = MagicMock()
    del mock_client_no_scripts.list_scripts 
    # Ensure hasattr returns False by deleting attributes isn't enough on MagicMock sometimes
    # So we'll just not add them. MagicMock creates attributes on access, so we need spec or manual delete and strict check.
    # Easiest way: Mock create_client to return an object that isn't a MagicMock for those methods or mocking the attr check.
    
    # Actually, the command checks `hasattr(client, "list_scripts")`.
    # MagicMock usually responds True to hasattr unless configured otherwise.
    mock_client_no_scripts = MagicMock(spec=[]) # Empty spec might work?
    
    # Let's just mock the behavior inside the test by using a real object or a restricted mock
    class MockSoftwareClient:
        pass
    
    mock_client = MockSoftwareClient()
    
    runner = CliRunner()
    with patch("dremio_cli.commands.script.create_client", return_value=mock_client):
        result = runner.invoke(cli, ["script", "list"])
        
    assert "not supported" in result.output
