
import click
from dremio_cli.config import ProfileManager
from dremio_cli.tui.catalog.app import CatalogApp

@click.group("ui")
def ui():
    """Interactive TUI commands."""
    pass

@ui.command("catalog")
@click.pass_context
def catalog_ui(ctx):
    """Launch interactive Catalog Explorer."""
    client = ctx.obj.client
    manager = ProfileManager()
    profile = manager.get_default_profile() or "default"
    
    app = CatalogApp(client=client, profile_name=profile)
    app.run()
