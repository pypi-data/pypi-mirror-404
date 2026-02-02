"""Tests for multi-statement SQL execution."""

import pytest
from unittest.mock import MagicMock, patch
from click.testing import CliRunner

from dremio_cli.cli import cli
from dremio_cli.commands.sql import _parse_sql_statements

class TestSQLParsing:
    """Test SQL parsing logic."""
    
    def test_basic_split(self):
        sql = "SELECT 1; SELECT 2"
        statements = _parse_sql_statements(sql)
        assert len(statements) == 2
        assert statements[0] == "SELECT 1"
        assert statements[1] == "SELECT 2"
        
    def test_with_comments(self):
        sql = """
        -- This is a comment
        SELECT 1;
        /* Block comment
           goes here */
        SELECT 2;
        -- Another comment at end
        """
        statements = _parse_sql_statements(sql)
        assert len(statements) == 2
        assert statements[0] == "SELECT 1"
        assert statements[1] == "SELECT 2"

    def test_inline_comments(self):
        # Verify standard usage where comment is at end of line
        sql = "SELECT 1; -- comment\nSELECT 2;"
        statements = _parse_sql_statements(sql)
        assert len(statements) == 2
        assert statements[0] == "SELECT 1"
        assert statements[1] == "SELECT 2"
        
        # Verify limitation: content after -- on same line is removed
        sql_limitation = "SELECT 1; -- comment ; SELECT 2"
        statements_lim = _parse_sql_statements(sql_limitation)
        assert len(statements_lim) == 1 # SELECT 2 is lost
        assert statements_lim[0] == "SELECT 1"

    def test_empty_cleanup(self):
        sql = ";; SELECT 1; ;"
        statements = _parse_sql_statements(sql)
        assert len(statements) == 1
        assert statements[0] == "SELECT 1"


@pytest.fixture
def mock_profile_manager():
    with patch("dremio_cli.commands.sql.ProfileManager") as mock:
        manager = mock.return_value
        manager.get_profile.return_value = {
            "base_url": "http://localhost",
            "auth": {"token": "test-token"}
        }
        yield mock

@pytest.fixture
def mock_client():
    with patch("dremio_cli.commands.sql.create_client") as mock:
        client = mock.return_value
        # Default success response
        client.execute_sql.return_value = {"id": "job_123"}
        client.get_job.return_value = {"jobState": "COMPLETED"}
        client.get_job_results.return_value = {"rows": [{"res": 1}], "rowCount": 1}
        yield client

class TestMultiStatementExecution:
    """Test execution flow."""
    
    def test_multi_statement_execution(self, mock_profile_manager, mock_client):
        runner = CliRunner()
        # Mock file reading
        with runner.isolated_filesystem():
            with open("test.sql", "w") as f:
                f.write("SELECT 1; SELECT 2")
            
            result = runner.invoke(cli, ["sql", "execute", "--file", "test.sql"], obj={"profile_name": "test"})
            
            assert result.exit_code == 0
            assert mock_client.execute_sql.call_count == 2
            
    def test_stop_on_error(self, mock_profile_manager, mock_client):
        runner = CliRunner()
        
        # Setup mock to fail on 2nd query
        # We need side_effect for execute_sql or get_job depending on where it fails.
        # Let's say execution submission works, but job fails.
        
        # Call 1: Job 1 COMPLETED
        # Call 2: Job 2 FAILED
        # Call 3: Should not happen
        
        mock_client.execute_sql.side_effect = [{"id": "job_1"}, {"id": "job_2"}, {"id": "job_3"}]
        
        def get_job_side_effect(job_id):
            if job_id == "job_1":
                return {"jobState": "COMPLETED"}
            elif job_id == "job_2":
                return {"jobState": "FAILED", "errorMessage": "Syntax Error"}
            return {"jobState": "COMPLETED"}
            
        mock_client.get_job.side_effect = get_job_side_effect
        
        with runner.isolated_filesystem():
            with open("test.sql", "w") as f:
                f.write("SELECT 1; SELECT 2; SELECT 3")
            
            result = runner.invoke(cli, ["sql", "execute", "--file", "test.sql"], obj={"profile_name": "test"})
            
            assert result.exit_code != 0 # Should fail
            assert min(mock_client.execute_sql.call_count, 2) == 2 # Should have called at least 2
            # Verify 3rd was NOT called? 
            # If implementation loop stops on exception, execute_sql for 3rd won't be called.
            # However, my implementation raises Abort on FAILED job state.
            
            # We can check specific calls
            args_list = mock_client.execute_sql.call_args_list
            stmts = [c[0][0] for c in args_list]
            assert "SELECT 1" in stmts[0]
            assert "SELECT 2" in stmts[1]
            assert len(stmts) == 2 # Stopped after 2nd

    def test_async_ignored_for_multi(self, mock_profile_manager, mock_client):
        runner = CliRunner()
        
        with runner.isolated_filesystem():
            with open("test.sql", "w") as f:
                f.write("SELECT 1; SELECT 2")
            
            result = runner.invoke(cli, ["sql", "execute", "--file", "test.sql", "--async"], obj={"profile_name": "test"})
            
            assert result.exit_code == 0
            # Should still wait (call get_job)
            assert mock_client.get_job.called
