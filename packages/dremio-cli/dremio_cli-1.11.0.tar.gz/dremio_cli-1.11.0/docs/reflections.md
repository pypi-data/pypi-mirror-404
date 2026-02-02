# Reflection Management

Manage Dremio reflections (Software and Cloud).

## Commands

### List Reflections

List all reflections.

```bash
dremio reflection list [OPTIONS]
```

**Options:**
- `--summary` - Show summary only

**Examples:**
```bash
dremio reflection list
dremio --output json reflection list
```

### Get Reflection

Get details of a specific reflection.

```bash
dremio reflection get <REFLECTION_ID>
```

**Examples:**
```bash
dremio reflection get abc-123-def-456
dremio reflection get abc-123-def-456 --output yaml
```

### Create Reflection

Create a reflection using a JSON definition.

```bash
dremio reflection create [OPTIONS]
```

**Options:**
- `--file PATH` - Path to JSON file containing reflection definition
- `--json STRING` - JSON string containing reflection definition

**Examples:**
```bash
# From file
dremio reflection create --file reflection_def.json

# From JSON string
dremio reflection create --json '{"name": "my_reflection", "datasetId": "...", "type": "RAW", ...}'
```

**Reflection Definition Format:**
Refer to Dremio API documentation for the full reflection object structure.

### Update Reflection

Update an existing reflection.

```bash
dremio reflection update <REFLECTION_ID> [OPTIONS]
```

**Options:**
- `--file PATH` - Path to JSON file containing updated reflection definition
- `--json STRING` - JSON string containing updated reflection definition

**Examples:**
```bash
dremio reflection update abc-123 --file update.json
```

### Delete Reflection

Delete a reflection.

```bash
dremio reflection delete <REFLECTION_ID>
```

**Examples:**
```bash
dremio reflection delete abc-123
```
