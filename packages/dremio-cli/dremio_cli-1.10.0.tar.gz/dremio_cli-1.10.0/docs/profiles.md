# Profile Management Guide

This guide covers how to create and manage Dremio CLI profiles using CLI commands, YAML configuration, or environment variables.

## 1. Quick Start: CLI Commands

The fastest way to set up profiles is using the `dremio profile create` command. Below are examples for every supported configuration.

### 1. Dremio Cloud (PAT)
*Requires Project ID from your URL (e.g., `app.dremio.cloud/projectId/<PROJECT_ID>/...`).*
*For Dremio Cloud, the CLI automatically attempts to exchange this PAT for a short-lived OAuth token for enhanced security.*

```bash
dremio profile create cloud-prod \
  --type cloud \
  --base-url https://api.dremio.cloud/v0 \
  --project-id 788baab4-3c3b-42da-9f1d-5cc6dc03147d \
  --auth-type pat \
  --token "dtYQ629..."
```

### 2. Dremio Cloud (Service User / Client Credentials)

For service accounts using Client ID and Secret (OAuth Client Credentials flow).

```bash
dremio profile create cloud-service \
  --type cloud \
  --base-url https://api.dremio.cloud \
  --project-id <PROJECT_ID> \
  --auth-type oauth \
  --client-id <CLIENT_ID> \
  --client-secret <CLIENT_SECRET>
```

### 3. Dremio Software (PAT)
*Recommended for production scripts and service accounts.*

```bash
dremio profile create software-prod \
  --type software \
  --base-url https://dremio.company.com \
  --auth-type pat \
  --token "96fVB..."
```

### 4. Dremio Software (Username/Password)

Legacy authentication for Dremio Software.

```bash
dremio profile create soft-auth \
  --type software \
  --base-url http://localhost:9047 \
  --auth-type username_password \
  --username <USERNAME> \
  --password <PASSWORD>
```

> **Note on Service Users**: To use a Service User (Cloud or Software), simply generate a Personal Access Token (PAT) for that service account and use the **PAT** profile type shown above. The CLI does not currently support automated Client Credentials exchange.

---

## 2. Comprehensive YAML Configuration

You can manage all your profiles in a single file: `~/.dremio/profiles.yaml`.

Below is a complete example configuration showing all supported profile types.

```yaml
# ~/.dremio/profiles.yaml
profiles:
  # 1. Dremio Cloud (Default)
  cloud-prod:
    type: cloud
    base_url: https://api.dremio.cloud/v0
    project_id: 788baab4-3c3b-42da-9f1d-5cc6dc03147d
    auth:
      type: pat
      token: dtYQ629xQRukYE+cOExuAUr6VbWI/B+bu2c6hd6WM7c63XOXQS++3S4T6dJPfA==

  # 2. Cloud Service Account (Recommended for Automation)
  cloud-service-bot:
    type: cloud
    base_url: https://api.dremio.cloud
    project_id: b5e7h8...
    auth:
      type: oauth
      client_id: <CLIENT_ID>
      client_secret: <CLIENT_SECRET>

  # 3. Dremio Software (Legacy/Corporate)
  software-prod:
    type: software
    base_url: https://dremio.corp.com
    auth:
      type: pat
      token: 96fVBEuWREyqyVAJ9EWlRfxWR7UZx32YWpe/uZ86P5K3MjduYb8a3wp12jYIUA==

  # 4. Dremio Software (Local Dev)
  software-local:
    type: software
    base_url: http://localhost:9047
    auth:
      type: username_password
      username: admin
      password: password123

# Set the active profile
default_profile: cloud-prod
```

### Profile Fields Guide

| Field | Description |
|-------|-------------|
| `type` | `cloud` or `software`. |
| `base_url` | API Endpoint. <br>• Cloud (US): `https://api.dremio.cloud/v0`<br>• Cloud (EU): `https://api.dremio.eu/v0`<br>• Software: `https://<host>:<port>` |
| `project_id`| **Cloud Only**. Found in the Cloud Console URL. |
| `auth.type` | • `pat`: Personal Access Token<br>• `oauth`: Client Credentials Flow (Service User)<br>• `username_password`: Software Only. |
| `auth.token`| The token string (for `pat`). |
| `auth.client_id`| OAuth Client ID (for `oauth`). |
| `auth.client_secret`| OAuth Client Secret (for `oauth`). |

---

## 3. Environment Variable Configuration

Ideal for CI/CD pipelines. Environment variables override the YAML file.

| variable | example |
|----------|---------|
| `DREMIO_PROFILE_{NAME}_TYPE` | `cloud` |
| `DREMIO_{NAME}_BASE_URL` | `https://api.dremio.cloud/v0` |
| `DREMIO_{NAME}_PROJECTID` | `788b...` |
| `DREMIO_{NAME}_AUTH_TYPE` | `pat` |
| `DREMIO_{NAME}_TOKEN` | `dtYQ...` |

### Example `.env`

```bash
DREMIO_CLOUD_TYPE=cloud
DREMIO_CLOUD_BASE_URL=https://api.dremio.cloud/v0
DREMIO_CLOUD_PROJECTID=788baab4-3c3b-42da-9f1d-5cc6dc03147d
DREMIO_CLOUD_AUTH_TYPE=pat
DREMIO_CLOUD_TOKEN=dtYQ629...
```
