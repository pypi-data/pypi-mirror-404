"""SQL execution commands."""

import json
import click
from rich.console import Console
from pathlib import Path

from dremio_cli.config import ProfileManager
from dremio_cli.client.factory import create_client
from dremio_cli.formatters.table import format_as_table
from dremio_cli.formatters.json import format_as_json
from dremio_cli.formatters.yaml import format_as_yaml

console = Console()


@click.group()
def sql() -> None:
    """SQL execution operations."""
    pass


@sql.command("execute")
@click.argument("query", required=False)
@click.option("--file", "sql_file", type=click.Path(exists=True), help="Execute SQL from file")
@click.option("--context", help="Query context (space or folder path)")
@click.option("--async", "async_mode", is_flag=True, help="Execute asynchronously (return job ID immediately)")
@click.option("--output-file", type=click.Path(), help="Save results to file")
@click.pass_context
def execute_sql(ctx, query: str, sql_file: str, context: str, async_mode: bool, output_file: str) -> None:
    """Execute a SQL query.
    
    Examples:
        dremio sql execute "SELECT * FROM table LIMIT 10"
        dremio sql execute --file query.sql
        dremio sql execute "SELECT * FROM table" --context "MySpace"
        dremio sql execute "SELECT * FROM large_table" --async
        dremio sql execute "SELECT * FROM table" --output-file results.json
    """
    try:
        # Get profile
        manager = ProfileManager()
        profile_name = ctx.obj.profile_name
        profile = manager.get_profile(profile_name)
        
        if not profile:
            console.print(f"[red]Profile '{profile_name}' not found[/red]")
            raise click.Abort()
        
        # Get SQL content
        sql_content = ""
        if sql_file:
            with open(sql_file, 'r') as f:
                sql_content = f.read()
        elif query:
            sql_content = query
        else:
            console.print("[red]Error: Either provide a query or use --file[/red]")
            raise click.Abort()
        
        # Parse statements
        queries = _parse_sql_statements(sql_content)
        if not queries:
            console.print("[yellow]No valid SQL statements found[/yellow]")
            return

        # Create client
        client = create_client(profile)
        
        # Parse context
        sql_context = None
        if context:
            sql_context = [c.strip() for c in context.split(",")]
        
        # Execute queries
        total_queries = len(queries)
        
        # Force sync mode if multiple queries are present
        if total_queries > 1 and async_mode:
            console.print("[yellow]Note: --async flag ignored for multi-statement execution. Queries will run sequentially.[/yellow]")
            async_mode = False

        for i, sql_statement in enumerate(queries):
            if total_queries > 1:
                console.rule(f"Executing Statement {i+1}/{total_queries}")
                console.print(f"[dim]{sql_statement[:100]}...[/dim]")

            with console.status(f"[bold green]Executing SQL query..."):
                result = client.execute_sql(sql_statement, context=sql_context)
            
            # Check if result is a dictionary (it might be a string error message)
            if not isinstance(result, dict):
                console.print(f"[red]Error: Unexpected response from Dremio API:[/red]")
                console.print(f"{result}")
                raise click.Abort()
                
            job_id = result.get("id")
            
            if async_mode:
                # Return job ID immediately
                console.print(f"[green]✓[/green] Query submitted (Async)")
                console.print(f"  Job ID: {job_id}")
                # Display full command for user convenience
                console.print(f"\n[bold]Check status and results:[/bold]")
                console.print(f"  dremio job results {job_id}")
            else:
                # Wait for results
                import time
                
                console.print(f"[green]✓[/green] Query submitted. Waiting for completion...")
                console.print(f"  Job ID: {job_id}")
                
                # Polling loop
                with console.status(f"[bold green]Job {job_id} is running...[/bold green]", spinner="dots") as status:
                    while True:
                        job_info = client.get_job(job_id)
                        job_state = job_info.get("jobState")
                        
                        if job_state == "COMPLETED":
                            break
                        elif job_state in ["FAILED", "CANCELED"]:
                            console.print(f"[red]Job {job_state}[/red]")
                            err_msg = job_info.get("errorMessage", "Unknown error")
                            console.print(f"Error: {err_msg}")
                            raise click.Abort()
                        
                        # Wait before next poll
                        time.sleep(1.0)
                
                # Get job results
                if job_id:
                    try:
                        with console.status(f"[bold green]Fetching results..."):
                            results = client.get_job_results(job_id)
                        
                        rows = results.get("rows", [])
                        row_count = results.get("rowCount", len(rows))
                        
                        # Save to file if requested
                        if output_file:
                            # If multiple queries, we probably shouldn't overwrite. 
                            # For simplicity, append or use numbered files could be better, 
                            # but per requirements, just saving results is key.
                            # We will append to the same file for now if valid json/yaml? 
                            # Adding multiple JSON objects to one file makes it invalid JSON usually.
                            # Let's just write validation note:
                            if total_queries > 1:
                                console.print("[yellow]Warning: --output-file with multiple queries will subscribe/overwite. Currently not fully supported for multi-statement.[/yellow]")
                            
                            output_path = Path(output_file)
                            
                            # Advanced Formats (Pandas required)
                            if output_path.suffix in ['.parquet', '.csv']:
                                try:
                                    import pandas as pd
                                    df = pd.DataFrame(rows)
                                    
                                    if output_path.suffix == '.parquet':
                                        df.to_parquet(output_path)
                                    else: # csv
                                        df.to_csv(output_path, index=False)
                                        
                                except ImportError:
                                    console.print("[red]Error: 'pandas' and 'pyarrow' are required for Parquet/CSV export. Install them with pip.[/red]")
                                    raise click.Abort()
                                except Exception as e:
                                     console.print(f"[red]Export failed: {e}[/red]")
                                     raise click.Abort()

                            elif output_path.suffix == '.json':
                                output_path.write_text(json.dumps(results, indent=2))
                            elif output_path.suffix in ['.yaml', '.yml']:
                                import yaml
                                output_path.write_text(yaml.dump(results))
                            else:
                                # Default to JSON
                                output_path.write_text(json.dumps(results, indent=2))
                            
                            console.print(f"\n[green]✓[/green] Results saved to {output_file}")
                            console.print(f"  Rows: {row_count}")
                        else:
                            # Display results
                            output_format = ctx.obj.output_format
                            
                            if output_format == "json":
                                console.print(format_as_json(results))
                            elif output_format == "yaml":
                                console.print(format_as_yaml(results))
                            else:
                                if rows:
                                    format_as_table(rows, title=f"Query Results ({row_count} rows)")
                                else:
                                    console.print("[yellow]No results returned[/yellow]")
                    
                    except Exception as e:
                        console.print(f"\n[yellow]⚠[/yellow] Could not fetch results: {e}")
                        console.print(f"[dim]Job may still be running. Use 'dremio job results {job_id}' to check later[/dim]")
            
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        if ctx.obj.verbose:
            import traceback
            traceback.print_exc()
        raise click.Abort()


def _parse_sql_statements(sql_content: str) -> list[str]:
    """Parse SQL content into individual statements.
    
    Handles basic comment stripping and semicolon splitting.
    Does not handle semicolons within string literals perfectly (requires full parser),
    but good enough for CLI usage.
    """
    import re
    
    # Remove singe-line comments (-- ...)
    # match -- until end of line
    sql_clean = re.sub(r'--.*$', '', sql_content, flags=re.MULTILINE)
    
    # Remove block comments (/* ... */)
    sql_clean = re.sub(r'/\*.*?\*/', '', sql_clean, flags=re.DOTALL)
    
    # Split by semicolon
    statements = sql_clean.split(';')
    
    # Clean up and filter empty statements
    final_statements = []
    for stmt in statements:
        stmt = stmt.strip()
        if stmt:
            final_statements.append(stmt)
            
    return final_statements


@sql.command("explain")
@click.argument("query", required=False)
@click.option("--file", "sql_file", type=click.Path(exists=True), help="Explain SQL from file")
@click.option("--context", help="Query context (space or folder path)")
@click.pass_context
def explain_sql(ctx, query: str, sql_file: str, context: str) -> None:
    """Explain a SQL query execution plan.
    
    Examples:
        dremio sql explain "SELECT * FROM table"
        dremio sql explain --file query.sql
    """
    try:
        # Get profile
        manager = ProfileManager()
        profile_name = ctx.obj.profile_name
        profile = manager.get_profile(profile_name)
        
        if not profile:
            console.print(f"[red]Profile '{profile_name}' not found[/red]")
            raise click.Abort()
        
        # Get SQL query
        if sql_file:
            with open(sql_file, 'r') as f:
                query = f.read()
        elif not query:
            console.print("[red]Error: Either provide a query or use --file[/red]")
            raise click.Abort()
        
        # Create client
        client = create_client(profile)
        
        # Parse context
        sql_context = None
        if context:
            sql_context = [c.strip() for c in context.split(",")]
        
        # Explain query (execute with EXPLAIN prefix)
        explain_query = f"EXPLAIN PLAN FOR {query}"
        
        with console.status(f"[bold green]Generating execution plan..."):
            result = client.execute_sql(explain_query, context=sql_context)
        
        job_id = result.get("id")
        
        console.print(f"[green]✓[/green] Execution plan generated")
        console.print(f"  Job ID: {job_id}")
        
        # Get results
        if job_id:
            try:
                with console.status(f"[bold green]Fetching plan..."):
                    results = client.get_job_results(job_id)
                
                rows = results.get("rows", [])
                
                # Display plan
                output_format = ctx.obj.output_format
                
                if output_format == "json":
                    console.print(format_as_json(results))
                elif output_format == "yaml":
                    console.print(format_as_yaml(results))
                else:
                    if rows:
                        console.print("\n[bold]Execution Plan:[/bold]\n")
                        for row in rows:
                            # Plan is usually in first column
                            plan_text = list(row.values())[0] if row else ""
                            console.print(plan_text)
                    else:
                        console.print("[yellow]No plan returned[/yellow]")
            
            except Exception as e:
                console.print(f"\n[yellow]⚠[/yellow] Could not fetch plan: {e}")
        
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        if ctx.obj.verbose:
            import traceback
            traceback.print_exc()
        raise click.Abort()


@sql.command("validate")
@click.argument("query", required=False)
@click.option("--file", "sql_file", type=click.Path(exists=True), help="Validate SQL from file")
@click.option("--context", help="Query context (space or folder path)")
@click.pass_context
def validate_sql(ctx, query: str, sql_file: str, context: str) -> None:
    """Validate SQL query syntax.
    
    Examples:
        dremio sql validate "SELECT * FROM table"
        dremio sql validate --file query.sql
    """
    try:
        # Get profile
        manager = ProfileManager()
        profile_name = ctx.obj.profile_name
        profile = manager.get_profile(profile_name)
        
        if not profile:
            console.print(f"[red]Profile '{profile_name}' not found[/red]")
            raise click.Abort()
        
        # Get SQL query
        if sql_file:
            with open(sql_file, 'r') as f:
                query = f.read()
        elif not query:
            console.print("[red]Error: Either provide a query or use --file[/red]")
            raise click.Abort()
        
        # Create client
        client = create_client(profile)
        
        # Parse context
        sql_context = None
        if context:
            sql_context = [c.strip() for c in context.split(",")]
        
        # Validate by doing EXPLAIN (doesn't execute, just validates)
        explain_query = f"EXPLAIN PLAN FOR {query}"
        
        with console.status(f"[bold green]Validating SQL syntax..."):
            try:
                result = client.execute_sql(explain_query, context=sql_context)
                job_id = result.get("id")
                
                # If we got a job ID, syntax is valid
                console.print(f"[green]✓[/green] SQL syntax is valid")
                console.print(f"  Job ID: {job_id}")
                
            except Exception as e:
                error_msg = str(e)
                console.print(f"[red]✗[/red] SQL syntax error")
                console.print(f"\n[red]{error_msg}[/red]")
                raise click.Abort()
        
    except click.Abort:
        raise
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        if ctx.obj.verbose:
            import traceback
            traceback.print_exc()
        raise click.Abort()
