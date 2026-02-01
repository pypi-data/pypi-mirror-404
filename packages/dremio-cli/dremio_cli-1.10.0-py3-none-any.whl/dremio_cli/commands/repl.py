"""Interactive SQL Shell (REPL)."""

import click
import os
from pathlib import Path
from rich.console import Console
from rich.table import Table

from prompt_toolkit import PromptSession
from prompt_toolkit.lexers import PygmentsLexer
from pygments.lexers.sql import SqlLexer
from prompt_toolkit.styles import Style
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.history import FileHistory

from dremio_cli.config import ProfileManager
from dremio_cli.client.factory import create_client

console = Console()

SQL_KEYWORDS = [
    'SELECT', 'FROM', 'WHERE', 'GROUP BY', 'ORDER BY', 'LIMIT',
    'JOIN', 'LEFT JOIN', 'RIGHT JOIN', 'INNER JOIN', 'OUTER JOIN',
    'AND', 'OR', 'NOT', 'IN', 'IS NULL', 'IS NOT NULL',
    'COUNT', 'SUM', 'AVG', 'MIN', 'MAX',
    'CREATE', 'view', 'DROP', 'ALTER', 'UPDATE', 'DELETE',
    'WITH', 'AS', 'ON', 'DISTINCT', 'show'
]

@click.command("repl")
@click.pass_context
def repl_command(ctx):
    """Start an interactive SQL shell."""
    
    # Setup Client
    profile_manager = ProfileManager()
    profile_name = ctx.obj.profile_name
    profile = profile_manager.get_profile(profile_name)
    
    if not profile:
        console.print(f"[red]Profile '{profile_name}' not found[/red]")
        return

    client = create_client(profile)
    
    console.print(f"[bold cyan]Dremio SQL Shell ({profile_name})[/bold cyan]")
    console.print("Type 'exit' or 'quit' to leave. Semicolon not required.")

    # REPL Setup
    history_file = Path.home() / ".dremio_history"
    session = PromptSession(
        history=FileHistory(str(history_file)),
        lexer=PygmentsLexer(SqlLexer),
        completer=WordCompleter(SQL_KEYWORDS, ignore_case=True)
    )

    while True:
        try:
            text = session.prompt('dremio> ')
            text = text.strip()
            
            if not text:
                continue
                
            if text.lower() in ('exit', 'quit'):
                break
                
            if text.lower() == 'clear':
                console.clear()
                continue
            
            # Execute
            with console.status("Executing..."):
                try:
                    # Simple execute - assumes SELECT for now mostly
                    # We reuse logic from sql execution but simplified
                    result = client.execute_sql(text)
                    
                    # If async job id returned
                    if isinstance(result, dict) and 'id' in result:
                        job_id = result['id']
                        # polling...
                        final_result = client.get_job_results(job_id)
                        
                        rows = final_result.get("rows", [])
                        count = final_result.get("rowCount", len(rows))
                        
                        if rows:
                            table = Table()
                            # Columns
                            cols = rows[0].keys()
                            for col in cols:
                                table.add_column(col)
                            
                            for row in rows:
                                table.add_row(*[str(row.get(c, "")) for c in cols])
                                
                            console.print(table)
                        else:
                            console.print("[yellow]No rows returned.[/yellow]")
                            
                        console.print(f"[dim]Rows: {count}[/dim]")
                        
                except Exception as e:
                     console.print(f"[red]Error: {e}[/red]")

        except KeyboardInterrupt:
            continue
        except EOFError:
            break
            
    console.print("Goodbye!")
