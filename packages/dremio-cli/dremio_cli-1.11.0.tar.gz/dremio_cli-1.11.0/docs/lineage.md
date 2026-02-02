# Lineage Visualization

Visualize the dependencies between datasets.

## Commands

### Show Lineage

Show the upstream parents of a dataset.

```bash
dremio lineage show <CATALOG_ID> [OPTIONS]
```

**Options:**
- `--format [tree|json|mermaid]` - Output format (Default: tree)

**Examples:**
```bash
# Tree view (Terminal)
dremio lineage show dremio-catalog.space.view

# Mermaid Graph (for markdown)
dremio lineage show dremio-catalog.space.view --format mermaid
```
