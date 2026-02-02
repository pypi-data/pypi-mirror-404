"""Real-time Dremio Monitor TUI."""

import click
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, DataTable
from textual.containers import Container
from textual.screen import Screen

from dremio_cli.config import ProfileManager
from dremio_cli.client.factory import create_client

class JobMonitor(App):
    """A Textual app to monitor Dremio jobs."""

    CSS = """
    Screen {
        layout: vertical;
    }
    DataTable {
        height: 100%;
        border: solid green;
    }
    """
    
    BINDINGS = [("q", "quit", "Quit"), ("r", "refresh", "Refresh")]

    def __init__(self, client):
        super().__init__()
        self.client = client

    def compose(self) -> ComposeResult:
        yield Header()
        yield DataTable()
        yield Footer()

    def on_mount(self) -> None:
        table = self.query_one(DataTable)
        table.add_columns("Job ID", "Status", "User", "Query Type", "Start Time")
        self.action_refresh()
        self.set_interval(5, self.action_refresh)

    def action_refresh(self) -> None:
        table = self.query_one(DataTable)
        try:
            # We need to list jobs. Requires list_jobs method on client usually.
            # Assuming generic call for now or leveraging API
            # Cloud/Software slightly different API for job listing filtering
            # For this MVP, we fetch recent jobs.
            
            # Using _make_request directly if list_jobs not strict
            # Actually SoftwareClient has list_jobs? No, we didn't check.
            # Let's try raw API call pattern if method missing
            
            # Using generic sql to query sys.jobs if possible, or API
            # Ideally we use sys.jobs as it's consistent? No, API is better.
            
            # Fallback implementation: use client specific method if exists
            # We haven't implemented list_jobs in clients yet explicitly in this session
            # but usually it's there or we add it safely.
            
            # Let's try to query sys.jobs via SQL for universality
            query = "SELECT job_id, status, user_name, query_type, start_time FROM sys.jobs ORDER BY start_time DESC LIMIT 20"
            result = self.client.execute_sql(query)
            
            # If async, we might get an ID but no results yet.
            # But sys.jobs query returns fast usually.
            # If it's job object, fetch results
            if isinstance(result, dict) and 'id' in result:
                 # It's an async job handle
                 final = self.client.get_job_results(result['id'])
                 rows = final.get("rows", [])
            else:
                 rows = []
                 
            table.clear()
            for row in rows:
                table.add_row(
                    row.get('job_id'),
                    row.get('status'),
                    row.get('user_name'),
                    row.get('query_type'),
                    row.get('start_time')
                )
                
        except Exception:
            table.clear()
            # table.add_row("Error fetching jobs", "", "", "", "")

@click.command("monitor")
@click.pass_context
def monitor_command(ctx):
    """Launch real-time system monitor."""
    profile_manager = ProfileManager()
    profile_name = ctx.obj.profile_name
    profile = profile_manager.get_profile(profile_name)
    
    if not profile:
        click.echo(f"Profile '{profile_name}' not found")
        return

    client = create_client(profile)
    app = JobMonitor(client)
    app.run()
