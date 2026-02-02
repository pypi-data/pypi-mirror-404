
import os
import click
from dremio_cli.utils.console import console
from dremio_cli.dac.config import DremioConfig
from dremio_cli.dac.sync import DremioSync

@click.group(help="Dremio-as-Code synchronization.")
def sync():
    pass

@sync.command("pull")
@click.option("--config", default="dremio.yaml", help="Path to dremio.yaml config file.")
@click.pass_context
def pull(ctx, config):
    """Pull state from Dremio to local filesystem."""
    try:
        if not os.path.exists(config):
            console.print(f"[red]Config file '{config}' not found. Please create a dremio.yaml first.[/red]")
            return

        conf = DremioConfig.load(config)
        client = ctx.obj
        
        syncer = DremioSync(conf, client, os.path.dirname(os.path.abspath(config)))
        syncer.pull()
        
    except Exception as e:
        console.print(f"[red]Pull failed: {e}[/red]")
        # import traceback
        # traceback.print_exc()

@sync.command("push")
@click.option("--config", default="dremio.yaml", help="Path to dremio.yaml config file.")
@click.option("--dry-run", is_flag=True, help="Show changes without applying them.")
@click.pass_context
def push(ctx, config, dry_run):
    """Push local state to Dremio."""
    try:
        if not os.path.exists(config):
             console.print(f"[red]Config file '{config}' not found.[/red]")
             return

        conf = DremioConfig.load(config)
        client = ctx.obj
        
        syncer = DremioSync(conf, client, os.path.dirname(os.path.abspath(config)))
        syncer.push(dry_run=dry_run)

    except Exception as e:
        console.print(f"[red]Push failed: {e}[/red]")
