"""SpaceOps CLI - CI/CD for Databricks Genie spaces."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import click
import yaml
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table

from . import __version__
from .benchmark import (
    generate_benchmark_report,
    load_benchmark_suite,
    run_benchmark_suite,
)
from .client import GenieAPIError, GenieClient
from .diff import compute_diff, parse_serialized_space, print_diff
from .models import (
    BenchmarkSuiteResult,
    EnvironmentConfig,
    PromotionConfig,
    SpaceDefinition,
)

console = Console()


def load_space_definition(path: Path) -> SpaceDefinition:
    """Load a space definition from YAML or JSON file."""
    with open(path) as f:
        data = yaml.safe_load(f) if path.suffix in (".yaml", ".yml") else json.load(f)
    return SpaceDefinition(**data)


def load_env_config(path: Path) -> EnvironmentConfig:
    """Load environment configuration from YAML file."""
    with open(path) as f:
        data = yaml.safe_load(f)
    return EnvironmentConfig(**data)


def load_promotion_config(path: Path) -> PromotionConfig:
    """Load promotion configuration from YAML file."""
    with open(path) as f:
        data = yaml.safe_load(f)
    return PromotionConfig(**data)


def _clean_snapshot_output(data: dict) -> dict:
    """Clean up snapshot output for better readability.

    The API returns content and sql as lists of strings (one per line).
    This function joins them into single readable strings.
    """

    def join_string_list(items):
        """Join a list of strings into a single string."""
        if isinstance(items, list) and all(isinstance(i, str) for i in items):
            return "".join(items).strip()
        return items

    def process_dict(d):
        """Recursively process dictionary to clean up string lists."""
        if not isinstance(d, dict):
            return d

        result = {}
        for key, value in d.items():
            if key in ("content", "sql", "question") and isinstance(value, list):
                # Join string lists into single strings
                result[key] = join_string_list(value)
            elif isinstance(value, dict):
                result[key] = process_dict(value)
            elif isinstance(value, list):
                result[key] = [
                    process_dict(item) if isinstance(item, dict) else item for item in value
                ]
            else:
                result[key] = value
        return result

    return process_dict(data)


def get_client(host: str | None = None, token: str | None = None) -> GenieClient:
    """Create a Genie API client."""
    return GenieClient(host=host, token=token)


@click.group()
@click.version_option(version=__version__, prog_name="spaceops")
def main():
    """SpaceOps - CI/CD for Databricks Genie spaces.

    Manage, version, test, and promote Genie spaces across environments.
    """
    pass


@main.command()
@click.argument("space_id")
@click.option("-o", "--output", type=click.Path(), help="Output file path")
@click.option(
    "--format", "fmt", type=click.Choice(["yaml", "json"]), default="yaml", help="Output format"
)
@click.option("--host", envvar="DATABRICKS_HOST", help="Databricks workspace host")
@click.option("--token", envvar="DATABRICKS_TOKEN", help="Databricks access token")
def snapshot(space_id: str, output: str | None, fmt: str, host: str | None, token: str | None):
    """Snapshot a Genie space configuration for backup or version control.

    Exports the complete space configuration including tables, joins,
    instructions, and examples using include_serialized_space=true.

    Example:
        spaceops snapshot 01f0f8550b05141f8e58021028559422 -o spaces/billing/space.yaml
    """
    try:
        with get_client(host, token) as client:
            console.print(f"[dim]Fetching space {space_id}...[/dim]")
            space = client.get_space(space_id, include_serialized=True)

            # Parse the serialized space
            serialized = {}
            if space.serialized_space:
                serialized = parse_serialized_space(space.serialized_space)

            # Build the space definition
            definition = {
                "title": space.title,
                "warehouse_id": space.warehouse_id,
                "description": getattr(space, "description", None),
                **serialized,
            }

            # Clean up None values
            definition = {k: v for k, v in definition.items() if v is not None}

            # Post-process to make YAML more readable
            definition = _clean_snapshot_output(definition)

            if fmt == "yaml":
                # Use literal block style for multi-line strings
                def str_representer(dumper, data):
                    if "\n" in data:
                        return dumper.represent_scalar("tag:yaml.org,2002:str", data, style="|")
                    return dumper.represent_scalar("tag:yaml.org,2002:str", data)

                yaml.add_representer(str, str_representer)
                content = yaml.dump(
                    definition, default_flow_style=False, sort_keys=False, allow_unicode=True
                )
            else:
                content = json.dumps(definition, indent=2)

            if output:
                output_path = Path(output)
                output_path.parent.mkdir(parents=True, exist_ok=True)
                output_path.write_text(content)
                console.print(f"[green]✓[/green] Snapshot saved to [bold]{output}[/bold]")
            else:
                syntax = Syntax(content, fmt, theme="monokai")
                console.print(syntax)

            # Print summary
            tables = serialized.get("data_sources", {}).get("tables", [])
            console.print(
                Panel(
                    f"[bold]Space:[/bold] {space.title}\n"
                    f"[bold]ID:[/bold] {space.space_id}\n"
                    f"[bold]Warehouse:[/bold] {space.warehouse_id}\n"
                    f"[bold]Tables:[/bold] {len(tables)}",
                    title="📸 Snapshot Summary",
                    border_style="green",
                )
            )

    except GenieAPIError as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)


@main.command()
@click.argument("definition_path", type=click.Path(exists=True))
@click.option("--space-id", help="Existing space ID to update (creates new if not provided)")
@click.option("--warehouse-id", help="Override warehouse ID from definition")
@click.option("--env", type=click.Path(exists=True), help="Environment config file")
@click.option("--dry-run", is_flag=True, help="Show what would be done without making changes")
@click.option("--host", envvar="DATABRICKS_HOST", help="Databricks workspace host")
@click.option("--token", envvar="DATABRICKS_TOKEN", help="Databricks access token")
def push(
    definition_path: str,
    space_id: str | None,
    warehouse_id: str | None,
    env: str | None,
    dry_run: bool,
    host: str | None,
    token: str | None,
):
    """Push a space definition to Databricks.

    Creates a new space if --space-id is not provided, otherwise updates
    the existing space.

    Example:
        spaceops push spaces/billing/space.yaml --space-id abc123
        spaceops push spaces/billing/space.yaml --env config/prod.yaml
    """
    try:
        definition = load_space_definition(Path(definition_path))

        # Apply environment overrides
        if env:
            env_config = load_env_config(Path(env))
            space_id = space_id or env_config.space_id
            warehouse_id = warehouse_id or env_config.warehouse_id
            host = host or env_config.host

            # Apply table mappings if configured
            if env_config.table_mappings and definition.data_sources:
                for table in definition.data_sources.tables:
                    if table.identifier in env_config.table_mappings:
                        table.identifier = env_config.table_mappings[table.identifier]

        action = "update" if space_id else "create"

        console.print(
            Panel(
                f"[bold]Action:[/bold] {action.upper()}\n"
                f"[bold]Title:[/bold] {definition.title}\n"
                f"[bold]Space ID:[/bold] {space_id or '(new)'}\n"
                f"[bold]Warehouse:[/bold] {warehouse_id or definition.warehouse_id}\n"
                f"[bold]Tables:[/bold] {len(definition.data_sources.tables)}",
                title=f"{'🔍 Dry Run' if dry_run else '🚀 Push'} Preview",
                border_style="yellow" if dry_run else "blue",
            )
        )

        if dry_run:
            console.print("[yellow]Dry run - no changes made[/yellow]")
            return

        with get_client(host, token) as client:
            result = client.push_space(definition, space_id=space_id, warehouse_id=warehouse_id)

            console.print(f"[green]✓[/green] Space {action}d successfully!")
            console.print(f"  [bold]Space ID:[/bold] {result.space_id}")
            console.print(f"  [bold]Title:[/bold] {result.title}")

    except GenieAPIError as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)


@main.command()
@click.argument("definition_path", type=click.Path(exists=True))
@click.argument("space_id")
@click.option("--host", envvar="DATABRICKS_HOST", help="Databricks workspace host")
@click.option("--token", envvar="DATABRICKS_TOKEN", help="Databricks access token")
def diff(definition_path: str, space_id: str, host: str | None, token: str | None):
    """Compare local definition with remote space.

    Shows what changes would be applied if you push the local definition.

    Example:
        spaceops diff spaces/billing/space.yaml 01f0f8550b05141f8e58021028559422
    """
    try:
        definition = load_space_definition(Path(definition_path))

        with get_client(host, token) as client:
            console.print(f"[dim]Fetching remote space {space_id}...[/dim]")
            remote_space = client.get_space(space_id, include_serialized=True)

            # Parse configurations
            local_config = definition.to_serialized_space().model_dump()
            remote_config = {}
            if remote_space.serialized_space:
                remote_config = parse_serialized_space(remote_space.serialized_space)

            # Compute diff
            diff_result = compute_diff(local_config, remote_config)

            console.print(f"\n[bold]Comparing:[/bold] {definition_path} ↔ {remote_space.title}")
            print_diff(local_config, remote_config, diff_result)

            if diff_result.has_changes:
                sys.exit(1)  # Exit with error code for CI usage

    except GenieAPIError as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)


@main.command()
@click.argument("definition_path", type=click.Path(exists=True))
def validate(definition_path: str):
    """Validate a space definition file.

    Checks that the definition is valid YAML/JSON and conforms to the schema.

    Example:
        spaceops validate spaces/billing/space.yaml
    """
    try:
        definition = load_space_definition(Path(definition_path))

        # Validation checks
        errors = []
        warnings = []

        if not definition.title:
            errors.append("Missing required field: title")

        if not definition.data_sources.tables:
            warnings.append("No tables defined in data_sources")

        # Check for duplicate table identifiers
        table_ids = [t.identifier for t in definition.data_sources.tables]
        duplicates = [t for t in table_ids if table_ids.count(t) > 1]
        if duplicates:
            errors.append(f"Duplicate table identifiers: {set(duplicates)}")

        # Check table identifiers format (catalog.schema.table)
        for table in definition.data_sources.tables:
            parts = table.identifier.split(".")
            if len(parts) != 3:
                warnings.append(
                    f"Table identifier '{table.identifier}' should be fully qualified (catalog.schema.table)"
                )

        # Print results
        if errors:
            console.print("[red]✗ Validation failed[/red]")
            for err in errors:
                console.print(f"  [red]ERROR:[/red] {err}")
            for warn in warnings:
                console.print(f"  [yellow]WARNING:[/yellow] {warn}")
            sys.exit(1)
        else:
            console.print("[green]✓ Validation passed[/green]")
            if warnings:
                for warn in warnings:
                    console.print(f"  [yellow]WARNING:[/yellow] {warn}")

            # Print summary
            console.print(
                Panel(
                    f"[bold]Title:[/bold] {definition.title}\n"
                    f"[bold]Tables:[/bold] {len(definition.data_sources.tables)}\n"
                    f"[bold]Joins:[/bold] {len(definition.joins)}\n"
                    f"[bold]Instructions:[/bold] {len(definition.instructions)}\n"
                    f"[bold]Examples:[/bold] {len(definition.example_queries)}\n"
                    f"[bold]Functions:[/bold] {len(definition.functions)}",
                    title="✓ Valid Space Definition",
                    border_style="green",
                )
            )

    except Exception as e:
        console.print(f"[red]✗ Validation failed:[/red] {e}")
        sys.exit(1)


@main.command()
@click.argument("space_id")
@click.argument("benchmark_paths", nargs=-1, type=click.Path(exists=True))
@click.option("--min-accuracy", type=float, default=0.8, help="Minimum required accuracy (0-1)")
@click.option("--output", type=click.Path(), help="Output report file")
@click.option("--format", "fmt", type=click.Choice(["markdown", "json"]), default="markdown")
@click.option("--host", envvar="DATABRICKS_HOST", help="Databricks workspace host")
@click.option("--token", envvar="DATABRICKS_TOKEN", help="Databricks access token")
def benchmark(
    space_id: str,
    benchmark_paths: tuple[str, ...],
    min_accuracy: float,
    output: str | None,
    fmt: str,
    host: str | None,
    token: str | None,
):
    """Run benchmark tests against a Genie space.

    Executes a suite of test queries and validates that Genie generates
    correct SQL. Useful for CI/CD to block promotion if accuracy drops.

    Example:
        spaceops benchmark abc123 benchmarks/queries.yaml --min-accuracy 0.9
    """
    if not benchmark_paths:
        console.print("[red]Error:[/red] At least one benchmark file is required")
        sys.exit(1)

    try:
        results: list[BenchmarkSuiteResult] = []

        with get_client(host, token) as client:
            for path in benchmark_paths:
                suite = load_benchmark_suite(Path(path))
                suite.min_accuracy = min_accuracy

                result = run_benchmark_suite(client, space_id, suite, verbose=True)
                results.append(result)

        # Generate report
        report = generate_benchmark_report(results, fmt)

        if output:
            Path(output).write_text(report)
            console.print(f"[green]✓[/green] Report saved to {output}")

        # Check overall pass/fail
        all_passed = all(r.accuracy >= min_accuracy for r in results)

        if not all_passed:
            console.print(f"\n[red]✗ Benchmark failed - accuracy below {min_accuracy:.0%}[/red]")
            sys.exit(1)
        else:
            console.print(
                f"\n[green]✓ All benchmarks passed (>= {min_accuracy:.0%} accuracy)[/green]"
            )

    except GenieAPIError as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)


@main.command()
@click.argument("definition_path", type=click.Path(exists=True))
@click.argument("target_env")
@click.option("--config", type=click.Path(exists=True), required=True, help="Promotion config file")
@click.option(
    "--benchmark",
    "benchmark_path",
    type=click.Path(exists=True),
    help="Benchmark file to run before promotion",
)
@click.option("--min-accuracy", type=float, default=0.8, help="Minimum accuracy for benchmark")
@click.option("--skip-benchmark", is_flag=True, help="Skip benchmark validation")
@click.option("--dry-run", is_flag=True, help="Show what would be done")
@click.option("--force", is_flag=True, help="Force promotion even if benchmarks fail")
def promote(
    definition_path: str,
    target_env: str,
    config: str,
    benchmark_path: str | None,
    min_accuracy: float,
    skip_benchmark: bool,
    dry_run: bool,
    force: bool,
):
    """Promote a space definition to a target environment.

    Validates the space, optionally runs benchmarks, and pushes to the
    target environment with appropriate overrides.

    Example:
        spaceops promote spaces/billing/space.yaml prod --config config/promotion.yaml
    """
    try:
        promotion_config = load_promotion_config(Path(config))

        if target_env not in promotion_config.environments:
            available = ", ".join(promotion_config.environments.keys())
            console.print(
                f"[red]Error:[/red] Unknown environment '{target_env}'. Available: {available}"
            )
            sys.exit(1)

        env_config = promotion_config.environments[target_env]
        definition = load_space_definition(Path(definition_path))

        console.print(
            Panel(
                f"[bold]Target:[/bold] {target_env}\n"
                f"[bold]Host:[/bold] {env_config.host}\n"
                f"[bold]Space:[/bold] {env_config.space_id or '(new)'}\n"
                f"[bold]Warehouse:[/bold] {env_config.warehouse_id}",
                title="🚀 Promotion Plan",
                border_style="blue",
            )
        )

        # Run benchmark if configured
        if benchmark_path and not skip_benchmark:
            console.print("\n[bold]Running pre-promotion benchmarks...[/bold]")

            # Use the source environment for benchmarks (typically dev/stage)
            env_order = promotion_config.promotion_order
            current_idx = env_order.index(target_env) if target_env in env_order else 0

            if current_idx > 0:
                source_env = env_order[current_idx - 1]
                source_config = promotion_config.environments.get(source_env)

                if source_config and source_config.space_id:
                    with GenieClient(host=source_config.host) as client:
                        suite = load_benchmark_suite(Path(benchmark_path))
                        suite.min_accuracy = min_accuracy
                        result = run_benchmark_suite(
                            client, source_config.space_id, suite, verbose=True
                        )

                        if result.accuracy < min_accuracy:
                            if force:
                                console.print(
                                    "[yellow]Warning:[/yellow] Benchmark failed but --force specified"
                                )
                            else:
                                console.print("[red]✗ Benchmark failed - blocking promotion[/red]")
                                sys.exit(1)

        if dry_run:
            console.print("\n[yellow]Dry run - no changes made[/yellow]")
            return

        # Apply environment-specific overrides
        if env_config.table_mappings and definition.data_sources:
            for table in definition.data_sources.tables:
                if table.identifier in env_config.table_mappings:
                    console.print(
                        f"  Remapping table: {table.identifier} → {env_config.table_mappings[table.identifier]}"
                    )
                    table.identifier = env_config.table_mappings[table.identifier]

        # Push to target environment
        with GenieClient(host=env_config.host) as client:
            result = client.push_space(
                definition,
                space_id=env_config.space_id,
                warehouse_id=env_config.warehouse_id,
            )

            console.print(f"\n[green]✓ Successfully promoted to {target_env}![/green]")
            console.print(f"  [bold]Space ID:[/bold] {result.space_id}")

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)


@main.command("list")
@click.option("--host", envvar="DATABRICKS_HOST", help="Databricks workspace host")
@click.option("--token", envvar="DATABRICKS_TOKEN", help="Databricks access token")
def list_spaces(host: str | None, token: str | None):
    """List all Genie spaces in the workspace."""
    try:
        with get_client(host, token) as client:
            spaces, _ = client.list_spaces()

            if not spaces:
                console.print("[dim]No spaces found[/dim]")
                return

            table = Table(title="Genie Spaces", show_header=True, header_style="bold magenta")
            table.add_column("Space ID")
            table.add_column("Title")
            table.add_column("Warehouse ID")

            for space in spaces:
                table.add_row(space.space_id, space.title, space.warehouse_id)

            console.print(table)

    except GenieAPIError as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)


@main.command()
@click.argument("space_id")
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation")
@click.option("--host", envvar="DATABRICKS_HOST", help="Databricks workspace host")
@click.option("--token", envvar="DATABRICKS_TOKEN", help="Databricks access token")
def delete(space_id: str, yes: bool, host: str | None, token: str | None):
    """Delete a Genie space."""
    try:
        with get_client(host, token) as client:
            # Get space details first
            space = client.get_space(space_id, include_serialized=False)

            if not yes:
                console.print(
                    f"[yellow]Warning:[/yellow] This will delete space '{space.title}' ({space_id})"
                )
                if not click.confirm("Are you sure?"):
                    console.print("Cancelled")
                    return

            client.delete_space(space_id)
            console.print(f"[green]✓[/green] Deleted space {space_id}")

    except GenieAPIError as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
