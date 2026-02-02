
from textual.widgets import Tree, TabbedContent, TabPane, Markdown, DataTable, Static
from textual.widgets.tree import TreeNode
from textual import work
from rich.text import Text

class CatalogTree(Tree):
    """Tree widget for Dremio Catalog."""

    def __init__(self, client):
        super().__init__("Dremio Catalog")
        self.client = client
        self.root.expand()

    def on_mount(self) -> None:
        """Load initial root items."""
        self.load_roots()

    @work(thread=True)
    def load_roots(self) -> None:
        """Fetch root catalog items."""
        try:
            # Get catalog roots
            catalog = self.client.get_catalog()
            data = catalog.get("data", [])
            
            for item in data:
                # Determine icon/color
                itype = item.get("type", "UNKNOWN")
                icon = "📁"
                if itype == "SOURCE": icon = "🔌"
                elif itype == "SPACE": icon = "🪐"
                elif itype == "HOME": icon = "🏠"
                elif itype == "CONTAINER": 
                     # Could be anything, try to infer or just use generic
                     icon = "📦"
                
                label = Text(f"{icon} {item.get('path', ['?'])[-1]}")
                
                # Add node
                node = self.root.add(label, data=item, expand=False)
                # Add dummy child to allow expansion if it's a container
                if itype in ["SOURCE", "SPACE", "HOME", "FOLDER", "CONTAINER"]:
                    node.allow_expand = True
                    node.add("Loading...", data=None)

        except Exception as e:
            self.notify(f"Error loading catalog: {e}", severity="error")

    async def on_tree_node_expanded(self, event: Tree.NodeExpanded) -> None:
        """Load children when node expanded."""
        node = event.node
        if node.data is None: return # Root or dummy
        
        # If we have a dummy child "Loading...", let's fetch real children
        if len(node.children) == 1 and node.children[0].label == "Loading...":
             self.load_children(node)

    @work(thread=True)
    def load_children(self, node: TreeNode) -> None:
        """Fetch children for a node."""
        item = node.data
        item_id = item.get("id")
        
        if not item_id: return

        try:
            # We need to remove the dummy node first - but safely
            # Since we are in a thread, we should schedule UI update
            self.app.call_from_thread(node.remove_children)
            
            # Fetch children
            # catalog/{id} usually returns children for containers
            details = self.client.get_catalog_item(item_id)
            children = details.get("children", [])
            
            if not children:
                self.app.call_from_thread(node.add, "-(Empty)-", data=None)
                return

            for child in children:
                ctype = child.get("type", "UNKNOWN")
                name = child.get("path", ["?"])[-1]
                
                icon = "📄" # Dataset default
                allow_expand = False
                
                if ctype == "FOLDER": 
                    icon = "📁"
                    allow_expand = True
                elif ctype == "DATASET" or ctype == "VIRTUAL_DATASET" or ctype == "PHYSICAL_DATASET":
                    icon = "📊"
                elif ctype == "FILE":
                    icon = "📑"

                label = Text(f"{icon} {name}")
                
                # Add via main thread
                new_node = self.app.call_from_thread(node.add, label, data=child, allow_expand=allow_expand)
                
                if allow_expand:
                    self.app.call_from_thread(new_node.add, "Loading...", data=None)

        except Exception as e:
            self.app.notify(f"Error loading children: {e}", severity="error")


class DetailPane(Static):
    """Pane for showing details of selected catalog item."""

    def compose(self):
        with TabbedContent(initial="info"):
            with TabPane("Info", id="info"):
                yield Markdown("# Select an item", id="info-md")
            with TabPane("Schema", id="schema"):
                yield DataTable(id="schema-table")
            with TabPane("SQL", id="sql"):
                yield Static("", id="sql-view")
            with TabPane("Preview", id="preview"):
                yield DataTable(id="preview-table")

    def on_mount(self):
        # Setup tables
        schema_table = self.query_one("#schema-table", DataTable)
        schema_table.add_columns("Name", "Type")
        
        preview_table = self.query_one("#preview-table", DataTable)
        preview_table.cursor_type = "row"

    def update_info(self, item_data: dict, full_details: dict = None):
        """Update info tab."""
        path = ".".join(item_data.get("path", []))
        itype = item_data.get("entityType", "UNKNOWN")
        iid = item_data.get("id", "N/A")
        
        md = f"""
# {path}
**Type**: {itype}
**ID**: {iid}
"""
        if full_details:
             if "createdAt" in full_details:
                 md += f"\n**Created**: {full_details.get('createdAt')}"
             if "owner" in full_details:
                 md += f"\n**Owner**: {full_details.get('owner')}"

        self.query_one("#info-md", Markdown).update(md)

    def update_sql(self, sql: str):
        self.query_one("#sql-view", Static).update(sql or "-- No SQL --")

    def update_schema(self, columns: list):
        table = self.query_one("#schema-table", DataTable)
        table.clear()
        if not columns: return
        
        for col in columns:
            name = col.get("name", "?")
            ctype = col.get("type", {}).get("name", "UNKNOWN")
            table.add_row(name, ctype)

    def update_preview(self, rows: list, columns: list):
        table = self.query_one("#preview-table", DataTable)
        table.clear(columns=True)
        
        if not columns: 
            table.add_columns("No Data")
            return

        table.add_columns(*columns)
        for row in rows:
            # Row is dict usually from execute_sql result
            row_data = [str(row.get(col, "")) for col in columns]
            table.add_row(*row_data)

    def clear(self):
        self.query_one("#info-md", Markdown).update("# Select an item")
        self.query_one("#schema-table", DataTable).clear()
        self.query_one("#sql-view", Static).update("")
        self.query_one("#preview-table", DataTable).clear(columns=True)
