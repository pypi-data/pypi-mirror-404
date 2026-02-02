# Query History

View and manage your local query execution history.

## Commands

### List History

List recent query history.

```bash
dremio history list [OPTIONS]
```

**Options:**
- `--limit INT` - Maximum number of entries to show (Default: 50)

**Examples:**
```bash
dremio history list
dremio history list --limit 10
```

### Run History

Re-run a command from history.

```bash
dremio history run <HISTORY_ID>
```

**Examples:**
```bash
dremio history run 5
```

### Clear History

Clear all query history.

```bash
dremio history clear
```

**Examples:**
```bash
dremio history clear
```
