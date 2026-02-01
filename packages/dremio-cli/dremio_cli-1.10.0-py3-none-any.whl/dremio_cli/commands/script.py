"""Script management commands."""

import json
import click
from rich.console import Console
from typing import Optional

from dremio_cli.config import ProfileManager
from dremio_cli.client.factory import create_client
from dremio_cli.formatters.table import format_as_table
from dremio_cli.formatters.json import format_as_json
from dremio_cli.formatters.yaml import format_as_yaml

console = Console()


@click.group()
def script() -> None:
    """Script management operations (Cloud only)."""
    pass


@script.command("list")
@click.option("--limit", default=25, help="Number of results to return")
@click.option("--offset", default=0, help="Offset for pagination")
@click.pass_context
def list_scripts(ctx, limit: int, offset: int) -> None:
    """List scripts.
    
    Examples:
        dremio script list
        dremio script list --limit 10
    """
    try:
        # Get profile
        manager = ProfileManager()
        profile_name = ctx.obj.profile_name
        profile = manager.get_profile(profile_name)
        
        if not profile:
            console.print(f"[red]Profile '{profile_name}' not found[/red]")
            raise click.Abort()
        
        # Create client
        client = create_client(profile)
        
        # Check if client supports scripts
        if not hasattr(client, "list_scripts"):
             console.print("[yellow]Script operations are not supported by this Dremio environment (Software).[/yellow]")
             return

        # Get scripts
        with console.status(f"[bold green]Fetching scripts..."):
            data = client.list_scripts(limit=limit, offset=offset)
        
        items = data.get("data", [])

        # Format output
        output_format = ctx.obj.output_format
        
        if output_format == "json":
            console.print(format_as_json(items))
        elif output_format == "yaml":
            console.print(format_as_yaml(items))
        else:
            if items:
                format_as_table(items, title="Scripts")
            else:
                console.print("[yellow]No scripts found[/yellow]")
            
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        if ctx.obj.verbose:
            import traceback
            traceback.print_exc()
        raise click.Abort()


@script.command("get")
@click.argument("script_id")
@click.pass_context
def get_script(ctx, script_id: str) -> None:
    """Get script by ID.
    
    Examples:
        dremio script get abc-123
    """
    try:
        # Get profile
        manager = ProfileManager()
        profile_name = ctx.obj.profile_name
        profile = manager.get_profile(profile_name)
        
        if not profile:
            console.print(f"[red]Profile '{profile_name}' not found[/red]")
            raise click.Abort()
        
        # Create client
        client = create_client(profile)

        if not hasattr(client, "get_script"):
             console.print("[yellow]Script operations are not supported by this Dremio environment (Software).[/yellow]")
             return
        
        # Get script
        with console.status(f"[bold green]Fetching script {script_id}..."):
            data = client.get_script(script_id)
        
        # Format output
        output_format = ctx.obj.output_format
        
        if output_format == "json":
            console.print(format_as_json(data))
        elif output_format == "yaml":
            console.print(format_as_yaml(data))
        else:
            format_as_table(data, title=f"Script: {script_id}")
            # Also print content for scripts which is useful
            if "content" in data:
                console.print("\n[bold]Content:[/bold]")
                console.print(data["content"])
            
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        if ctx.obj.verbose:
            import traceback
            traceback.print_exc()
        raise click.Abort()


@script.command("create")
@click.option("--name", required=True, help="Script name")
@click.option("--content", required=True, help="SQL content")
@click.option("--context", help="Context as list content (comma separated)")
@click.pass_context
def create_script(ctx, name: str, content: str, context: Optional[str]) -> None:
    """Create a script.
    
    Examples:
        dremio script create --name "My Script" --content "SELECT 1"
    """
    try:
        # Get profile
        manager = ProfileManager()
        profile_name = ctx.obj.profile_name
        profile = manager.get_profile(profile_name)
        
        if not profile:
            console.print(f"[red]Profile '{profile_name}' not found[/red]")
            raise click.Abort()
        
        # Create client
        client = create_client(profile)
        
        if not hasattr(client, "create_script"):
             console.print("[yellow]Script operations are not supported by this Dremio environment (Software).[/yellow]")
             return

        context_list = context.split(",") if context else None

        # Create script
        with console.status("[bold green]Creating script..."):
            result = client.create_script(name, content, context_list)
        
        script_id = result.get("id")
        
        console.print(f"[green]✓[/green] Script created successfully")
        console.print(f"  ID: {script_id}")
        
        # Display full result if verbose
        if ctx.obj.verbose:
            output_format = ctx.obj.output_format
            if output_format == "json":
                console.print(format_as_json(result))
            elif output_format == "yaml":
                console.print(format_as_yaml(result))
            
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        if ctx.obj.verbose:
            import traceback
            traceback.print_exc()
        raise click.Abort()


@script.command("update")
@click.argument("script_id")
@click.option("--name", required=True, help="Script name")
@click.option("--content", required=True, help="SQL content")
@click.option("--context", help="Context")
@click.pass_context
def update_script(ctx, script_id: str, name: str, content: str, context: Optional[str]) -> None:
    """Update a script.
    
    Examples:
        dremio script update abc-123 --name "Updated Name" --content "SELECT 2"
    """
    try:
        # Get profile
        manager = ProfileManager()
        profile_name = ctx.obj.profile_name
        profile = manager.get_profile(profile_name)
        
        if not profile:
            console.print(f"[red]Profile '{profile_name}' not found[/red]")
            raise click.Abort()
        
        # Create client
        client = create_client(profile)
        
        if not hasattr(client, "update_script"):
             console.print("[yellow]Script operations are not supported by this Dremio environment (Software).[/yellow]")
             return

        context_list = context.split(",") if context else None

        # Update script
        with console.status(f"[bold green]Updating script {script_id}..."):
            result = client.update_script(script_id, name, content, context_list)
        
        console.print(f"[green]✓[/green] Script updated successfully")
        
        # Display full result if verbose
        if ctx.obj.verbose:
            output_format = ctx.obj.output_format
            if output_format == "json":
                console.print(format_as_json(result))
            elif output_format == "yaml":
                console.print(format_as_yaml(result))
            
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        if ctx.obj.verbose:
            import traceback
            traceback.print_exc()
        raise click.Abort()


@script.command("delete")
@click.argument("script_id")
@click.confirmation_option(prompt="Are you sure you want to delete this script?")
@click.pass_context
def delete_script(ctx, script_id: str) -> None:
    """Delete a script.
    
    Examples:
        dremio script delete abc-123
    """
    try:
        # Get profile
        manager = ProfileManager()
        profile_name = ctx.obj.profile_name
        profile = manager.get_profile(profile_name)
        
        if not profile:
            console.print(f"[red]Profile '{profile_name}' not found[/red]")
            raise click.Abort()
        
        # Create client
        client = create_client(profile)
        
        if not hasattr(client, "delete_script"):
             console.print("[yellow]Script operations are not supported by this Dremio environment (Software).[/yellow]")
             return

        # Delete script
        with console.status(f"[bold yellow]Deleting script {script_id}..."):
            client.delete_script(script_id)
        
        console.print(f"[green]✓[/green] Script deleted successfully")
            
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        if ctx.obj.verbose:
            import traceback
            traceback.print_exc()
        raise click.Abort()
