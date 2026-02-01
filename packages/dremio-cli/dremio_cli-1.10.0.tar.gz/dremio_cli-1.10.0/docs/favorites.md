# Favorite Queries

Manage and re-run your favorite SQL queries.

## Commands

### Add Favorite

Save a query as a favorite.

```bash
dremio favorite add <NAME> [OPTIONS]
```

**Options:**
- `--sql TEXT` - The SQL query to save (Required)
- `--description TEXT` - A brief description of the query

**Examples:**
```bash
dremio favorite add daily_sales --sql "SELECT * FROM sales WHERE date = CURRENT_DATE"
dremio favorite add top_users --sql "SELECT * FROM users ORDER BY score DESC LIMIT 10" --description "Top 10 users by score"
```

### List Favorites

List all saved favorite queries.

```bash
dremio favorite list [OPTIONS]
```

**Examples:**
```bash
dremio favorite list
dremio --output json favorite list
```

### Run Favorite

Execute a saved favorite query.

```bash
dremio favorite run <NAME>
```

**Examples:**
```bash
dremio favorite run daily_sales
```

### Delete Favorite

Remove a query from favorites.

```bash
dremio favorite delete <NAME>
```

**Examples:**
```bash
dremio favorite delete daily_sales
```
