
# Data Validations in Dremio-as-Code

Ensure data quality and integrity by defining SQL assertions that run after every `sync push`.

## Overview

Validations are SQL queries paired with a condition. The CLI executes the query, fetches the scalar result (first column of first row), and compares it against your condition.

## YAML Schema

Add a `validations` block to any dataset YAML (`VIRTUAL_DATASET` or `ICEBERG_TABLE`).

```yaml
name: "mart_revenue"
type: VIRTUAL_DATASET
path: ["dremio", "finance", "mart_revenue"]
sql: "SELECT ..."

validations:
  # Check 1: Non-zero rows
  - name: "row_count"
    sql: "SELECT count(*) FROM dremio.finance.mart_revenue"
    condition: "gt 0"

  # Check 2: No null regions
  - name: "no_null_regions"
    sql: "SELECT count(*) FROM dremio.finance.mart_revenue WHERE region IS NULL"
    condition: "eq 0"

  # Check 3: Total is positive
  - name: "positive_revenue"
    sql: "SELECT min(total_revenue) FROM dremio.finance.mart_revenue"
    condition: "gte 0"
```

## Supported Conditions

-   `eq {val}`: Equal to value
-   `neq {val}`: Not equal to value
-   `gt {val}`: Greater than value
-   `lt {val}`: Less than value
-   `gte {val}`: Greater than or equal to value
-   `lte {val}`: Less than or equal to value

## Workflow

1.  Sync (Create/Update View/Table).
2.  Wait for completion.
3.  **Run Validations**:
    -   Execute Check SQL.
    -   Fetch Result.
    -   Evaluate Condition.
    -   Log `[PASS]` or `[FAIL]`.
