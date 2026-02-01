
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer
from textual.binding import Binding
from dremio_cli.tui.catalog.screens import CatalogScreen

class CatalogApp(App):
    """Dremio Catalog Explorer TUI Application."""

    CSS = """
    Screen {
        layout: horizontal;
    }
    """
    
    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("r", "refresh", "Refresh"),
    ]

    def __init__(self, client, profile_name: str, **kwargs):
        super().__init__(**kwargs)
        self.client = client
        self.profile_name = profile_name

    def compose(self) -> ComposeResult:
        yield Header()
        yield CatalogScreen()
        yield Footer()

    def action_refresh(self) -> None:
        """Refresh the catalog tree."""
        # TODO: Implement refresh
        self.query_one("CatalogScreen").refresh_catalog()
