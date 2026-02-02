
# Managing Tables in Dremio-as-Code

DAC supports managing Physical Iceberg Tables and standard Physical Datasets.

## 1. Iceberg Tables (`type: ICEBERG_TABLE`)

You can use DAC to manage the lifecycle of Dremio-native Iceberg tables (e.g., in Arctic, Nessie, or S3). This allows for "Lightweight ETL" where every `push` triggers an SQL update script.

### YAML Schema

```yaml
name: "app_events"
type: ICEBERG_TABLE
path: ["dremio", "etl", "app_events"]

# Run ONE-TIME if table doesn't exist
create_sql: |
  CREATE TABLE dremio.etl.app_events (
    id VARCHAR, 
    event_time TIMESTAMP, 
    payload VARCHAR
  ) PARTITION BY (event_time)

# Run EVERY PUSH (if table exists)
update_sql: |
  MERGE INTO dremio.etl.app_events t 
  USING source.raw_events s 
  ON t.id = s.id
  WHEN MATCHED THEN UPDATE SET t.payload = s.payload
  WHEN NOT MATCHED THEN INSERT VALUES (s.id, s.event_time, s.payload)

# Standard features
tags: ["events", "etl"]
governance: ...
reflections: ...
```

### Workflow
1.  **First Push**: CLI detects missing table. executes `create_sql`.
2.  **Subsequent Pushes**: CLI detects existing table. Executes `update_sql`.

### Pulling Iceberg Tables
`dremio sync pull` will generate the YAML for existing Iceberg tables.
*Limitation*: The CLI cannot reconstruct the `create_sql` or `update_sql` logic. The fields will be generated as placeholders or comments.

## 2. Physical Datasets (`type: PHYSICAL_DATASET`)

For external files (S3 Parquet/CSV) or RDBMS tables that are read-only to Dremio, use `PHYSICAL_DATASET`. DAC manages their **metadata** (Governance, Reflections, Wiki), not their data lifecycle.

### YAML Schema

```yaml
name: "raw_customers"
type: PHYSICAL_DATASET
path: ["s3-source", "bucket", "customers.parquet"]

# Metadata
tags: ["raw", "source"]
description: "docs/raw_customers.md"

# Format (Optional - for auto-promotion)
format: 
  type: "Parquet"

# Governance
access_control:
  roles:
    - name: "analysts"
      privileges: ["SELECT"]
reflections:
  - name: "raw_ref"
    type: "RAW"
```

### Workflow
-   **Push**: Ensures the dataset is promoted/exists. Applies tags, wiki, grants, and reflections.
-   **Pull**: Generates YAML for existing promoted datasets in the scope.
