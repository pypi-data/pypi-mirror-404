"""Initialize CLI configuration."""

import click
import os
from getpass import getpass
from rich.console import Console
from rich.prompt import Prompt, Confirm

from dremio_cli.config import ProfileManager
from dremio_cli.client.factory import create_client

console = Console()

@click.command("init")
@click.pass_context
def init_command(ctx):
    """Interactive CLI initialization wizard."""
    console.rule("[bold cyan]Dremio CLI Setup[/bold cyan]")
    
    manager = ProfileManager()
    
    # Check existing
    config_path = manager.config_path
    if config_path.exists():
        console.print(f"Found existing configuration at: {config_path}")
        if not Confirm.ask("Do you want to add a new profile?", default=True):
            console.print("Exiting setup.")
            return

    # Profile Name
    name = Prompt.ask("Profile Name", default="default")
    
    # Platform
    ptype = Prompt.ask("Platform", choices=["software", "cloud"], default="software")
    
    # Base URL
    default_url = "https://api.dremio.cloud" if ptype == "cloud" else "http://localhost:9047"
    base_url = Prompt.ask("Base URL", default=default_url)
    
    # Credentials
    config = {
        "type": ptype,
        "base_url": base_url,
        "auth": {}
    }
    
    if ptype == "cloud":
        project_id = Prompt.ask("Project ID (Optional)", default="")
        if project_id:
            config["project_id"] = project_id
        
        token = getpass("Personal Access Token (PAT): ")
        config["auth"]["token"] = token
    else:
        auth_type = Prompt.ask("Auth Method", choices=["token", "basic"], default="basic")
        
        if auth_type == "token":
            token = getpass("Personal Access Token (PAT): ")
            config["auth"]["token"] = token
        else:
            username = Prompt.ask("Username")
            password = getpass("Password: ")
            config["auth"]["username"] = username
            config["auth"]["password"] = password

    # Verify
    console.print("\n[yellow]Verifying connection...[/yellow]")
    try:
        # Create temp profile obj for validation
        client = create_client(config)
        # Try a cheap call
        if ptype == "cloud":
            client.get_catalog() # Cloud doesn't have system info endpoint
        else:
            # For software we can try listing catalogs to prove auth works
            client.get_catalog()
            
        console.print("[green]✓ Connection Successful![/green]")
        
        # Save
        manager.add_profile(name, config)
        manager.save_config()
        
        # Set default if first one
        if not manager.get_default_profile():
            manager.set_default_profile(name)
            manager.save_config()
            console.print(f"[green]✓ Set '{name}' as default profile[/green]")
            
        console.print(f"\nConfiguration saved to: {config_path}")
        console.print("Run 'dremio catalog list' to get started!")

    except Exception as e:
        console.print(f"[red]✗ Connection Failed: {e}[/red]")
        if Confirm.ask("Save anyway?", default=False):
             manager.add_profile(name, config)
             manager.save_config()
             console.print(f"Configuration saved to: {config_path}")
