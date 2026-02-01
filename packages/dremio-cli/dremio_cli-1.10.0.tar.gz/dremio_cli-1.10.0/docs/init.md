# Interactive Initialization

Quickly set up your Dremio CLI configuration using an interactive wizard.

## Usage

```bash
dremio init
```

The wizard will guide you through:
1. Creating a new profile
2. Selecting platform (Cloud/Software)
3. Entering base URL and credentials
4. Verifying the connection immediately
5. Saving the profile and setting it as default

## Example Interaction

```text
Dremio CLI Setup
───────────────
Profile Name [default]: prod
Platform (software/cloud) [software]: cloud
Base URL [https://api.dremio.cloud]: 
Project ID: b49...
Personal Access Token (PAT): ********

Verifying connection...
✓ Connection Successful!

Configuration saved to: /Users/user/.dremio/profiles.yaml
Run 'dremio catalog list' to get started!
```
