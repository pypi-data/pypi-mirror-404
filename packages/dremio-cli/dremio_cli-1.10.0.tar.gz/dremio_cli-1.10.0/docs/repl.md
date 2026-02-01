# Interactive SQL Shell (REPL)

An enhanced interactive shell for executing SQL queries against Dremio.

## Features

- **Syntax Highlighting**: SQL keywords are highlighted as you type.
- **Persistent History**: Command history is saved across sessions (up arrow to recall).
- **Auto-completion**: Basic completion for SQL keywords.
- **Rich Output**: Results formatted in pretty tables.

## Usage

```bash
dremio repl
```

To exit, type `exit` or `quit`. To clear the screen, type `clear`.

## Commands

Inside the REPL, you can type any SQL query. Semicolons are optional.

```sql
dremio> SELECT * FROM "Space"."MyTable" LIMIT 5
```

You can also run other Dremio CLI commands by prefixing them with `dremio` (optional within REPL context logic depending on implementation, but standard SQL is primary).

*Note: The current implementation primarily focuses on SQL execution.*
