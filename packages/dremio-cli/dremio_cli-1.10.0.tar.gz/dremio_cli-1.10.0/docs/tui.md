# Catalog Explorer (TUI)

The Dremio CLI includes an interactive Terminal User Interface (TUI) for exploring your Dremio catalog, viewing schemas, and previewing data without leaving the command line.

## Usage

```bash
dremio ui catalog
```

Or using a specific profile:

```bash
dremio --profile prod ui catalog
```

## Features

### 1. Interactive Navigation
- **Tree View**: Navigate seamlessly through Spaces, Sources, Folders, and your Home directory.
- **Async Loading**: Large catalogs load quickly as you expand nodes.

### 2. Dataset Details
Select any dataset (View/Table) to see:
- **Info**: Metadata, ID, and Type.
- **Schema**: Column names and types.
- **SQL**: The underlying SQL definition (for Views).

### 3. Data Preview
- Switch to the **Preview** tab to instantly run a query (`SELECT * ... LIMIT 20`) and view actual data samples in a table.

## Controls

| Key | Action |
|-----|--------|
| `↑` / `↓` | Navigate Tree |
| `Space` | Expand/Collapse Folder |
| `Enter` | Select Item |
| `Click` | Select tabs (Info, Schema, Preview) |
| `q` | Quit |

## Requirements
- Dremio Software or Dremio Cloud
- Terminal with UTF-8 support
