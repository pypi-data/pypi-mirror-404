
from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Label, TabbedContent
from textual.containers import Vertical
from textual import work
from dremio_cli.tui.catalog.widgets import CatalogTree, DetailPane
import json # for debug

class CatalogScreen(Screen):
    """Main screen for Catalog Explorer."""
    
    CSS = """
    #sidebar {
        width: 30%;
        height: 100%;
        border-right: solid green;
    }
    #main-content {
        width: 70%;
        height: 100%;
    }
    """

    def compose(self) -> ComposeResult:
        yield Vertical(
            Label("Catalog Browser", id="tree-label"),
            CatalogTree(self.app.client),
            id="sidebar"
        )
        yield Vertical(
            DetailPane(id="details"),
            id="main-content"
        )
    
    async def on_tree_node_selected(self, event: CatalogTree.NodeSelected) -> None:
        """Handle tree selection."""
        item = event.node.data
        if not item: return

        pane = self.query_one(DetailPane)
        pane.clear()
        pane.update_info(item)
        
        # Determine if we should fetch more details (Schema/SQL)
        # Only for datasets
        itype = item.get("type", "")
        # Handle various API type strings
        valid_types = ["DATASET", "VIRTUAL_DATASET", "PHYSICAL_DATASET", "VIEW", "TABLE"]
        if itype in valid_types:
             self.fetch_dataset_details(item.get("id"))

    @work(thread=True)
    def fetch_dataset_details(self, dataset_id: str) -> None:
        """Fetch details for a dataset."""
        try:
            client = self.app.client
            # Get full catalog item
            details = client.get_catalog_item(dataset_id)
            
            pane = self.query_one(DetailPane)
            
            # Update Info
            self.app.call_from_thread(pane.update_info, details, details)
            
            # Update SQL
            sql = details.get("sql")
            self.app.call_from_thread(pane.update_sql, sql)
            
            # Update Schema
            fields = details.get("fields", [])
            self.app.call_from_thread(pane.update_schema, fields)
            
        except Exception as e:
            self.app.notify(f"Error fetching details: {e}", severity="error")

    async def on_tabbed_content_tab_activated(self, event: TabbedContent.TabActivated) -> None:
        """Handle tab switch."""
        if event.tab.id == "preview":
            # Check selected node
            tree = self.query_one(CatalogTree)
            if not tree.cursor_node or not tree.cursor_node.data:
                return
            
            item = tree.cursor_node.data
            itype = item.get("type", "")
            
            valid_types = ["DATASET", "VIRTUAL_DATASET", "PHYSICAL_DATASET", "VIEW", "TABLE"]
            if itype in valid_types:
                 self.fetch_preview(item)

    @work(thread=True)
    def fetch_preview(self, item: dict) -> None:
        """Fetch preview data."""
        path = ".".join(item.get("path", []))
        try:
             client = self.app.client
             # Run query with quotes around path for safety
             query_path = ".".join([f'"{p}"' for p in item.get("path", [])])
             res = client.execute_sql(f'SELECT * FROM {query_path} LIMIT 20')
             
             # API result format check: usually returns {'rows': [...], 'schema': [...]}
             rows = res.get("rows", [])
             
             columns = []
             if rows:
                 columns = list(rows[0].keys())
             elif "schema" in res:
                 columns = [f.get("name") for f in res.get("schema", [])]
             
             if not columns:
                 columns = ["Result"]

             pane = self.query_one(DetailPane)
             self.app.call_from_thread(pane.update_preview, rows, columns)
        except Exception as e:
            self.app.notify(f"Preview failed: {e}", severity="error")
