
# Managing Sources with Dremio-as-Code

DAC allows you to define and manage Dremio Sources (e.g., S3, Postgres, Nessie, Arctic) using YAML configuration files.

## Overview

- **Secure**: Use Environment Variable substitution (`${ENV_VAR}`) to keep credentials out of code.
- **Declarative**: Define the source configuration, and `dremio sync push` handles creation or updates.
- **Top-Level**: Sources are usually defined in the root of your DAC directory or a dedicated `sources/` folder.

## YAML Schema

```yaml
name: "my-source-name"
type: SOURCE
path: ["my-source-name"] # Must match name
source_type: "S3" # Dremio Source Type Code (e.g. S3, POSTGRES, NESSIE, ARCTIC, ADL)
config:
  # Source specific configuration
  accessKey: "${AWS_ACCESS_KEY}"
  secretKey: "${AWS_SECRET_KEY}"
  rootPath: "/"
metadata_policy:
  authTtlMs: 3600000
  ...
```

## Examples

### 1. Amazon S3

```yaml
name: "datalake-s3"
type: SOURCE
source_type: "S3"
config:
  accessKey: "${AWS_ACCESS_KEY}"
  secretKey: "${AWS_SECRET_KEY}" 
  secure: true
  rootPath: "/my-bucket/data"
```

### 2. Postgres

```yaml
name: "app-db"
type: SOURCE
source_type: "POSTGRES"
config:
  hostname: "db.production.internal"
  port: 5432
  username: "dremio_user"
  password: "${PG_PASSWORD}"
  databaseName: "myapp"
```

### 3. Nessie / Arctic

```yaml
name: "arctic-catalog"
type: SOURCE
source_type: "NESSIE"
config:
  endpoint: "https://nessie.dremio.cloud/v1/projects/${PROJECT_ID}"
  authType: "BEARER"
  token: "${NESSIE_TOKEN}"
```

## Environment Variables

Prior to running `dremio sync push`, ensure the referenced environment variables are set in your shell or `.env` file.

```bash
export AWS_ACCESS_KEY="AKI..."
export AWS_SECRET_KEY="secret..."
dremio sync push
```

If a variable is missing, the CLI will warn you and keep the literal string (which leads to auth failure), protecting you from accidental commits of unexpanded secrets.
