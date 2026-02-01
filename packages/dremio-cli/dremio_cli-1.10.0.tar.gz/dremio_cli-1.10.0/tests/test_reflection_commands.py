"""Tests for reflection commands."""

import json
from unittest.mock import MagicMock, patch
from click.testing import CliRunner
from dremio_cli.cli import cli


def test_list_reflections(mock_profile_manager, mock_client):
    """Test listing reflections."""
    mock_client.list_reflections.return_value = {"data": [{"id": "123", "name": "ref1"}]}
    
    runner = CliRunner()
    with patch("dremio_cli.commands.reflection.create_client", return_value=mock_client):
        result = runner.invoke(cli, ["reflection", "list"])
        
    assert result.exit_code == 0
    assert "ref1" in result.output
    mock_client.list_reflections.assert_called_once()


def test_get_reflection(mock_profile_manager, mock_client):
    """Test getting a reflection."""
    mock_client.get_reflection.return_value = {"id": "123", "name": "ref1"}
    
    runner = CliRunner()
    with patch("dremio_cli.commands.reflection.create_client", return_value=mock_client):
        result = runner.invoke(cli, ["reflection", "get", "123"])
        
    assert result.exit_code == 0
    assert "ref1" in result.output
    mock_client.get_reflection.assert_called_with("123")


def test_create_reflection_json(mock_profile_manager, mock_client):
    """Test creating a reflection from JSON string."""
    mock_client.create_reflection.return_value = {"id": "123", "name": "new_ref"}
    
    runner = CliRunner()
    json_data = '{"name": "new_ref", "datasetId": "456"}'
    
    with patch("dremio_cli.commands.reflection.create_client", return_value=mock_client):
        result = runner.invoke(cli, ["reflection", "create", "--json", json_data])
        
    assert result.exit_code == 0
    assert "created successfully" in result.output
    assert "123" in result.output
    mock_client.create_reflection.assert_called_with({"name": "new_ref", "datasetId": "456"})


def test_update_reflection(mock_profile_manager, mock_client):
    """Test updating a reflection."""
    mock_client.update_reflection.return_value = {"id": "123", "name": "updated_ref"}
    
    runner = CliRunner()
    json_data = '{"name": "updated_ref"}'
    
    with patch("dremio_cli.commands.reflection.create_client", return_value=mock_client):
        result = runner.invoke(cli, ["reflection", "update", "123", "--json", json_data])
        
    assert result.exit_code == 0
    assert "updated successfully" in result.output
    mock_client.update_reflection.assert_called_with("123", {"name": "updated_ref"})


def test_delete_reflection(mock_profile_manager, mock_client):
    """Test deleting a reflection."""
    runner = CliRunner()
    with patch("dremio_cli.commands.reflection.create_client", return_value=mock_client):
        result = runner.invoke(cli, ["reflection", "delete", "123", "--yes"])
        
    assert result.exit_code == 0
    assert "deleted successfully" in result.output
    mock_client.delete_reflection.assert_called_with("123")
