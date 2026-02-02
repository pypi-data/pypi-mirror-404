"""Shell completion generation."""

import click
import os

@click.command("completion")
@click.argument("shell", type=click.Choice(['bash', 'zsh', 'fish'], case_sensitive=False))
def completion_command(shell: str):
    """Generate shell completion scripts."""
    
    script = ""
    if shell == 'bash':
        script = '_DREMIO_COMPLETE=bash_source dremio'
        msg = "Add this to your .bashrc:\n\neval \"$(_DREMIO_COMPLETE=bash_source dremio)\""
    elif shell == 'zsh':
        script = '_DREMIO_COMPLETE=zsh_source dremio'
        msg = "Add this to your .zshrc:\n\neval \"$(_DREMIO_COMPLETE=zsh_source dremio)\""
    elif shell == 'fish':
        script = '_DREMIO_COMPLETE=fish_source dremio'
        msg = "Add this to your config.fish:\n\neval (env _DREMIO_COMPLETE=fish_source dremio)"
        
    click.echo(msg)
