# SpaceOps 🚀

**CI/CD for Databricks Genie Spaces — Multi-workspace promotion at scale**

SpaceOps provides a complete pipeline to define, version, test, and promote Genie spaces (knowledge store, joins, instructions, examples, functions, benchmarks) across dev/stage/prod environments.

## Why SpaceOps?

- **Version Control**: Store Genie space definitions as code in Git
- **Drift Control**: Detect and prevent configuration drift across environments
- **Benchmark Testing**: Block promotions if query accuracy drops
- **Multi-Workspace**: Promote spaces across dev → stage → prod with environment-specific overrides
- **Snapshots & Backups**: Export space state for auditing and disaster recovery

## Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/your-org/spaceops.git
cd spaceops

# Install dependencies
pip install -e .

# Verify installation
spaceops --version
```

### Environment Setup

```bash
export DATABRICKS_HOST="https://your-workspace.cloud.databricks.com"
export DATABRICKS_TOKEN="your-token"
```

### Basic Commands

```bash
# Snapshot an existing space
spaceops snapshot <space_id> -o spaces/my-space/space.yaml

# Validate a space definition
spaceops validate spaces/my-space/space.yaml

# Push to Databricks (create or update)
spaceops push spaces/my-space/space.yaml --space-id <existing_id>

# Compare local vs remote
spaceops diff spaces/my-space/space.yaml <space_id>

# Run benchmark tests
spaceops benchmark <space_id> spaces/my-space/benchmarks/accuracy.yaml

# Promote to an environment
spaceops promote spaces/my-space/space.yaml prod --config config/promotion.yaml
```

## Project Structure

```
spaceops/
├── spaceops/                 # Python package
│   ├── cli.py               # CLI commands
│   ├── client.py            # Databricks Genie API client
│   ├── models.py            # Pydantic data models
│   ├── diff.py              # Configuration diff utilities
│   └── benchmark.py         # Benchmark test runner
├── spaces/                   # Space definitions (version controlled)
│   └── billing/
│       ├── space.yaml       # Space configuration
│       └── benchmarks/
│           └── accuracy.yaml
├── config/                   # Environment configurations
│   ├── dev.yaml
│   ├── stage.yaml
│   ├── prod.yaml
│   └── promotion.yaml       # Multi-env promotion config
└── .github/workflows/
    └── genie-cicd.yaml      # CI/CD pipeline
```

## Space Definition Format

Space definitions are YAML files that define the complete configuration:

```yaml
title: "My Analytics Space"
description: "AI-powered analytics"
warehouse_id: null  # Set per-environment

data_sources:
  tables:
    - identifier: "catalog.schema.table"
      column_configs:
        - column_name: "id"
          enable_format_assistance: true
        - column_name: "category"
          enable_entity_matching: true

joins:
  - left_table: "catalog.schema.orders"
    right_table: "catalog.schema.customers"
    left_column: "customer_id"
    right_column: "id"
    join_type: "left"

instructions:
  - content: "When calculating revenue, use the net_amount column."
    category: "calculation"

example_queries:
  - question: "What was total revenue last month?"
    sql: "SELECT SUM(net_amount) FROM orders WHERE..."
```

## Benchmark Testing

Create benchmark suites to validate Genie's query accuracy:

```yaml
# benchmarks/accuracy.yaml
name: "Core Accuracy Tests"
min_accuracy: 0.8  # 80% must pass

queries:
  - question: "What was total usage last month?"
    expected_tables:
      - "system.billing.usage"
    expected_sql_contains:
      - "SUM"
      - "usage_quantity"

  - question: "Show costs by SKU"
    expected_tables:
      - "system.billing.usage"
      - "system.billing.list_prices"
    expected_sql_contains:
      - "JOIN"
```

Run benchmarks:

```bash
spaceops benchmark <space_id> benchmarks/accuracy.yaml --min-accuracy 0.9
```

## CI/CD Pipeline

The included GitHub Actions workflow provides:

1. **Validation** — Validates all space definitions on every PR
2. **Diff** — Shows what changes will be applied
3. **Dev Deploy** — Auto-deploys on merge to `develop`
4. **Stage Deploy** — Auto-deploys on merge to `main`
5. **Prod Deploy** — Requires manual approval + benchmark gates

### Required Secrets

| Secret | Description |
|--------|-------------|
| `DATABRICKS_DEV_HOST` | Dev workspace URL |
| `DATABRICKS_DEV_TOKEN` | Dev workspace token |
| `DATABRICKS_STAGE_HOST` | Stage workspace URL |
| `DATABRICKS_STAGE_TOKEN` | Stage workspace token |
| `DATABRICKS_PROD_HOST` | Prod workspace URL |
| `DATABRICKS_PROD_TOKEN` | Prod workspace token |
| `DEV_SPACE_ID` | Space ID in dev (after first deploy) |
| `STAGE_SPACE_ID` | Space ID in stage (after first deploy) |
| `PROD_SPACE_ID` | Space ID in prod (after first deploy) |

### Environment Protection

Configure GitHub environment protection rules:
- **production**: Require reviewers, restrict to `main` branch

## CLI Reference

### `spaceops snapshot`

Export a space configuration for backup or version control.

```bash
spaceops snapshot <space_id> [OPTIONS]

Options:
  -o, --output PATH    Output file path
  --format [yaml|json] Output format (default: yaml)
  --host TEXT          Databricks workspace host
  --token TEXT         Databricks access token
```

### `spaceops push`

Push a space definition to Databricks.

```bash
spaceops push <definition_path> [OPTIONS]

Options:
  --space-id TEXT      Existing space ID to update
  --warehouse-id TEXT  Override warehouse ID
  --env PATH           Environment config file
  --dry-run            Show what would be done
```

### `spaceops diff`

Compare local definition with remote space.

```bash
spaceops diff <definition_path> <space_id> [OPTIONS]
```

### `spaceops validate`

Validate a space definition file.

```bash
spaceops validate <definition_path>
```

### `spaceops benchmark`

Run benchmark tests against a Genie space.

```bash
spaceops benchmark <space_id> <benchmark_paths>... [OPTIONS]

Options:
  --min-accuracy FLOAT  Minimum required accuracy (0-1)
  --output PATH         Output report file
  --format [markdown|json]
```

### `spaceops promote`

Promote a space to a target environment.

```bash
spaceops promote <definition_path> <target_env> [OPTIONS]

Options:
  --config PATH        Promotion config file (required)
  --benchmark PATH     Benchmark file to run before promotion
  --min-accuracy FLOAT Minimum accuracy for benchmark
  --skip-benchmark     Skip benchmark validation
  --dry-run            Show what would be done
  --force              Force promotion even if benchmarks fail
```

### `spaceops list`

List all Genie spaces in the workspace.

```bash
spaceops list [OPTIONS]
```

### `spaceops delete`

Delete a Genie space.

```bash
spaceops delete <space_id> [OPTIONS]

Options:
  -y, --yes            Skip confirmation
```

## API Reference

SpaceOps uses the [Databricks Genie Management API](https://docs.databricks.com/api/workspace/genie):

- `GET /api/2.0/genie/spaces/{space_id}?include_serialized_space=true`
- `POST /api/2.0/genie/spaces`
- `PATCH /api/2.0/genie/spaces/{space_id}`
- `DELETE /api/2.0/genie/spaces/{space_id}`

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run with coverage
pytest --cov=spaceops
```

## License

MIT License - see LICENSE file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and linting
5. Submit a pull request

---

Built with ❤️ for the Databricks community

---

**Repository**: [github.com/charotAmine/databricks-spaceops](https://github.com/charotAmine/databricks-spaceops)

