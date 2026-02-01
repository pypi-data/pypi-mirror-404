"""Lineage management commands."""

import click
import json
from rich.console import Console
from rich.tree import Tree

from dremio_cli.config import ProfileManager
from dremio_cli.client.factory import create_client
from dremio_cli.formatters.json import format_as_json

console = Console()

@click.group()
def lineage():
    """Lineage visualization operations."""
    pass

@lineage.command("show")
@click.argument("catalog_id")
@click.option("--format", type=click.Choice(["tree", "json", "mermaid"], case_sensitive=False), default="tree", help="Output format")
@click.pass_context
def show_lineage(ctx, catalog_id: str, format: str):
    """Show lineage graph for a dataset.
    
    Examples:
        dremio lineage show <catalog-id>
        dremio lineage show <catalog-id> --format mermaid
    """
    try:
        manager = ProfileManager()
        profile_name = ctx.obj.profile_name
        profile = manager.get_profile(profile_name)
        
        if not profile:
            console.print(f"[red]Profile '{profile_name}' not found[/red]")
            return
            
        client = create_client(profile)
        
        try:
            graph = client.get_catalog_graph(catalog_id)
        except Exception as e:
            console.print(f"[red]Error fetching lineage: {e}[/red]")
            # Fallback or specific error handling (e.g. 404)
            return

        if format == "json":
            console.print(format_as_json(graph))
            return

        # Process graph for Tree/Mermaid
        # Graph structure usually: { "parents": [...], "children": [...] }
        # Or detailed nodes/edges depending on API version.
        # Assuming Dremio V3 graph response structure:
        # { "parents": [ { "id": "...", "path": [...] } ], "children": [] }
        
        # We focus on parents (upstream lineage)
        parents = graph.get("parents", [])
        
        if format == "mermaid":
            click.echo("graph TD")
            # Current node
            click.echo(f'    root["{catalog_id}"]')
            click.echo("    style root fill:#f9f,stroke:#333,stroke-width:2px")
            
            for parent in parents:
                p_path = ".".join(parent.get("path", []))
                p_id = parent.get("id", p_path) # fallback if id missing
                # Sanitize ID for mermaid
                safe_pid = p_id.replace("-", "_").replace(".", "_")
                
                click.echo(f'    {safe_pid}["{p_path}"] --> root')
                
        else: # tree
            tree = Tree(f"[bold cyan]{catalog_id}[/bold cyan]")
            if parents:
                p_branch = tree.add("Parents")
                for parent in parents:
                    p_path = ".".join(parent.get("path", []))
                    p_branch.add(f"[green]{p_path}[/green]")
            else:
                tree.add("[italic]No parents found[/italic]")
                
            console.print(tree)

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
