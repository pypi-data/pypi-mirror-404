
# Governance in Dremio-as-Code

DAC allows you to manage Access Control (RBAC) and Fine-Grained Access Control (Row/Column Policies) as code.

## 1. Access Control (RBAC)

Define who can access your dataset using the `access_control` block.

### YAML Schema

```yaml
name: "sensitive_data"
type: VIRTUAL_DATASET
...

access_control:
  roles:
    - name: "PUBLIC"
      privileges: ["SELECT"]
    - name: "finance_analysts"
      privileges: ["SELECT", "ALTER"]
  users:
    - name: "bob@example.com"
      privileges: ["SELECT"]
```

### Privileges
Common privileges include:
-   `SELECT`: Read data.
-   `ALTER`: Modify definition.
-   `MANAGE_GRANTS`: Change permissions.

### Workflow
-   **Push**: DAC resolves User/Role names to IDs and applies the grants.
-   *Note*: This **replaces** existing grants on the dataset.

## 2. Row Access Policies

Filter rows based on user context at query time.

### YAML Schema

```yaml
governance:
  row_access_policy:
    name: "dremio.security.region_policy"
    args: ["region_id"]
```

-   **name**: Full path to the UDF (User Defined Function) that implements the logic.
-   **args**: Columns from the dataset to pass as arguments to the UDF.

### UDF Example
You must create the UDF in Dremio first (or via `create_sql` in DAC).
```sql
CREATE FUNCTION dremio.security.region_policy (region_id VARCHAR)
RETURNS BOOLEAN
RETURN query_user() = 'admin' OR region_id = 'US'
```

## 3. Masking Policies (Column Level)

Mask sensitive column values.

### YAML Schema

```yaml
governance:
  masking_policies:
    - name: "dremio.security.mask_ssn"
      column: "ssn"
      args: ["ssn"]
    - name: "dremio.security.mask_email"
      column: "email"
      args: ["email"]
```

-   **name**: Full path to the Masking UDF.
-   **column**: The column to apply the mask to.
-   **args**: Columns to pass to the UDF.

### Workflow
-   **Push**: DAC executes `ALTER VIEW ... ADD ROW ACCESS POLICY` or `MODIFY COLUMN ... SET MASKING POLICY`.
-   **Limitations**:
    -   Only supported on Views (`VIRTUAL_DATASET`).
    -   Requires existing UDFs.
    -   Removing a policy from YAML does **not** automatically remove it from Dremio (requires manual `DROP` or `UNSET` logic, currently additive).
