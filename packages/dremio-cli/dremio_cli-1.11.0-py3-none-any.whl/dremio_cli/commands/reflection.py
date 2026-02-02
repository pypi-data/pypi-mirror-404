"""Reflection management commands."""

import json
import click
from rich.console import Console

from dremio_cli.config import ProfileManager
from dremio_cli.client.factory import create_client
from dremio_cli.formatters.table import format_as_table
from dremio_cli.formatters.json import format_as_json
from dremio_cli.formatters.yaml import format_as_yaml

console = Console()


@click.group()
def reflection() -> None:
    """Reflection management operations."""
    pass


@reflection.command("list")
@click.option("--summary", is_flag=True, help="Show summary only")
@click.pass_context
def list_reflections(ctx, summary: bool) -> None:
    """List reflections.
    
    Examples:
        dremio reflection list
        dremio reflection list --summary
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
        
        # Get reflections
        with console.status(f"[bold green]Fetching reflections..."):
            data = client.list_reflections(summary=summary)
        
        # Determine items list (API response structure varies)
        items = data.get("data", []) if isinstance(data, dict) else data
        if not items and isinstance(data, dict) and "id" in data: # Single item or different structure
             items = [data]
        if not items and isinstance(data, list):
            items = data

        # Format output
        output_format = ctx.obj.output_format
        
        if output_format == "json":
            console.print(format_as_json(items))
        elif output_format == "yaml":
            console.print(format_as_yaml(items))
        else:
            if items:
                format_as_table(items, title="Reflections")
            else:
                console.print("[yellow]No reflections found[/yellow]")
            
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        if ctx.obj.verbose:
            import traceback
            traceback.print_exc()
        raise click.Abort()


@reflection.command("get")
@click.argument("reflection_id")
@click.pass_context
def get_reflection(ctx, reflection_id: str) -> None:
    """Get reflection by ID.
    
    Examples:
        dremio reflection get abc-123
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
        
        # Get reflection
        with console.status(f"[bold green]Fetching reflection {reflection_id}..."):
            data = client.get_reflection(reflection_id)
        
        # Format output
        output_format = ctx.obj.output_format
        
        if output_format == "json":
            console.print(format_as_json(data))
        elif output_format == "yaml":
            console.print(format_as_yaml(data))
        else:
            format_as_table(data, title=f"Reflection: {reflection_id}")
            
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        if ctx.obj.verbose:
            import traceback
            traceback.print_exc()
        raise click.Abort()


@reflection.command("create")
@click.option("--file", "file_path", type=click.Path(exists=True), help="Path to JSON file with reflection definition")
@click.option("--json", "json_str", help="JSON string with reflection definition")
@click.pass_context
def create_reflection(ctx, file_path: str, json_str: str) -> None:
    """Create a reflection.
    
    Requires providing reflection definition via --file or --json.
    
    Examples:
        dremio reflection create --file reflection.json
    """
    try:
        if not file_path and not json_str:
            console.print("[red]Error: Must provide either --file or --json[/red]")
            raise click.Abort()

        # Parse definition
        if file_path:
            with open(file_path, "r") as f:
                reflection_data = json.load(f)
        else:
            reflection_data = json.loads(json_str)

        # Get profile
        manager = ProfileManager()
        profile_name = ctx.obj.profile_name
        profile = manager.get_profile(profile_name)
        
        if not profile:
            console.print(f"[red]Profile '{profile_name}' not found[/red]")
            raise click.Abort()
        
        # Create client
        client = create_client(profile)
        
        # Create reflection
        with console.status("[bold green]Creating reflection..."):
            result = client.create_reflection(reflection_data)
        
        reflection_id = result.get("id")
        
        console.print(f"[green]✓[/green] Reflection created successfully")
        console.print(f"  ID: {reflection_id}")
        
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


@reflection.command("update")
@click.argument("reflection_id")
@click.option("--file", "file_path", type=click.Path(exists=True), help="Path to JSON file with reflection definition")
@click.option("--json", "json_str", help="JSON string with reflection definition")
@click.pass_context
def update_reflection(ctx, reflection_id: str, file_path: str, json_str: str) -> None:
    """Update a reflection.
    
    Examples:
        dremio reflection update abc-123 --file update.json
    """
    try:
        if not file_path and not json_str:
            console.print("[red]Error: Must provide either --file or --json[/red]")
            raise click.Abort()

        # Parse definition
        if file_path:
            with open(file_path, "r") as f:
                reflection_data = json.load(f)
        else:
            reflection_data = json.loads(json_str)

        # Get profile
        manager = ProfileManager()
        profile_name = ctx.obj.profile_name
        profile = manager.get_profile(profile_name)
        
        if not profile:
            console.print(f"[red]Profile '{profile_name}' not found[/red]")
            raise click.Abort()
        
        # Create client
        client = create_client(profile)
        
        # Update reflection
        with console.status(f"[bold green]Updating reflection {reflection_id}..."):
            result = client.update_reflection(reflection_id, reflection_data)
        
        console.print(f"[green]✓[/green] Reflection updated successfully")
        
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


@reflection.command("delete")
@click.argument("reflection_id")
@click.confirmation_option(prompt="Are you sure you want to delete this reflection?")
@click.pass_context
def delete_reflection(ctx, reflection_id: str) -> None:
    """Delete a reflection.
    
    Examples:
        dremio reflection delete abc-123
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
        
        # Delete reflection
        with console.status(f"[bold yellow]Deleting reflection {reflection_id}..."):
            client.delete_reflection(reflection_id)
        
        console.print(f"[green]✓[/green] Reflection deleted successfully")
            
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        if ctx.obj.verbose:
            import traceback
            traceback.print_exc()
        raise click.Abort()
