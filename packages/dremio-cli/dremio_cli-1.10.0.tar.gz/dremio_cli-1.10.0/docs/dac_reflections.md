
# Managing Reflections in Dremio-as-Code

Reflections are Dremio's query acceleration technology. DAC allows you to define and manage reflections alongside your dataset definitions.

## YAML Schema

Add a `reflections` list to your Dataset YAML (`VIRTUAL_DATASET`, `ICEBERG_TABLE`, or `PHYSICAL_DATASET`).

```yaml
name: "orders"
type: VIRTUAL_DATASET
path: ["dremio", "business", "orders"]
sql: "SELECT * FROM source.orders"

reflections:
  # Raw Reflection
  - name: "raw_orders"
    type: "RAW"
    displayFields: ["order_id", "customer_id", "amount", "order_date"]
    partitionFields: ["order_date"]
    distributionFields: ["customer_id"]
    enabled: true

  # Aggregation Reflection
  - name: "agg_orders_by_customer"
    type: "AGGREGATION"
    dimensionFields: ["customer_id", "order_year"]
    measureFields: ["amount"]
    partitionFields: ["order_year"]
    distributionFields: ["customer_id"]
    enabled: true
```

## Reflection Types

### RAW
Accelerates detailed queries.
-   `displayFields`: List of columns to include.
-   `partitionFields`: Columns to partition the reflection by.
-   `distributionFields`: Columns to distribute data across nodes.

### AGGREGATION
Accelerates aggregate queries (GROUP BY).
-   `dimensionFields`: Columns used in GROUP BY.
-   `measureFields`: Columns used in aggregate functions (SUM, COUNT, etc.).
-   `partitionFields`: Partitioning configuration.
-   `distributionFields`: Distribution configuration.

## Workflow

1.  **Push**:
    -   DAC checks for existing reflections on the dataset.
    -   Matches by **Name**.
    -   **Update**: If found, updates configuration (enabled, fields).
    -   **Create**: If missing, creates the reflection.
2.  **Pull**:
    -   *Limitation*: Currently, pulling reflections from existing datasets is not fully supported. You must define them manually in your YAML.

## Best Practices
-   Use descriptive names (e.g., `agg_by_region`).
-   Keep definitions in the same YAML file as the View/Table.
-   Use `enabled: false` to disable a reflection without deleting the definition.
