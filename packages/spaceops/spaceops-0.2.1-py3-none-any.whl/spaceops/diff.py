"""Diff utilities for comparing Genie space configurations."""

from __future__ import annotations

import json
from dataclasses import dataclass
from enum import Enum
from typing import Any

from deepdiff import DeepDiff
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table
from rich.text import Text


class ChangeType(Enum):
    """Type of change detected in a diff."""

    ADDED = "added"
    REMOVED = "removed"
    MODIFIED = "modified"
    UNCHANGED = "unchanged"


@dataclass
class DiffResult:
    """Result of comparing two space configurations."""

    has_changes: bool
    changes: dict[str, Any]
    summary: str

    # Detailed breakdowns
    tables_added: list[str]
    tables_removed: list[str]
    tables_modified: list[str]
    instructions_changed: bool
    joins_changed: bool
    examples_changed: bool
    functions_changed: bool


def parse_serialized_space(serialized: str | dict) -> dict:
    """Parse a serialized space configuration."""
    if isinstance(serialized, str):
        return json.loads(serialized)
    return serialized


def normalize_config(config: dict) -> dict:
    """Normalize a config dict for comparison - treat None, [], {} as equivalent."""
    result = {}
    for key, value in config.items():
        if value is None or value == [] or value == {}:
            continue  # Skip empty values
        elif isinstance(value, dict):
            normalized = normalize_config(value)
            if normalized:  # Only include non-empty dicts
                result[key] = normalized
        elif isinstance(value, list):
            normalized_list = []
            for item in value:
                if isinstance(item, dict):
                    normalized_item = normalize_config(item)
                    if normalized_item:
                        normalized_list.append(normalized_item)
                elif item is not None:
                    normalized_list.append(item)
            if normalized_list:  # Only include non-empty lists
                result[key] = normalized_list
        else:
            result[key] = value
    return result


def compute_diff(
    local: dict,
    remote: dict,
    ignore_order: bool = True,
) -> DiffResult:
    """Compute the difference between local and remote space configurations.

    Args:
        local: Local space configuration.
        remote: Remote space configuration.
        ignore_order: Whether to ignore list ordering differences.

    Returns:
        DiffResult with detailed change information.
    """
    # Normalize both configs to treat empty values consistently
    local_normalized = normalize_config(local)
    remote_normalized = normalize_config(remote)

    diff = DeepDiff(
        remote_normalized,
        local_normalized,
        ignore_order=ignore_order,
        report_repetition=True,
        verbose_level=2,
    )

    has_changes = bool(diff)

    # Extract table changes using normalized configs
    tables_added = []
    tables_removed = []
    tables_modified = []

    local_tables = {
        t.get("identifier", ""): normalize_config(t)
        for t in local_normalized.get("data_sources", {}).get("tables", [])
    }
    remote_tables = {
        t.get("identifier", ""): normalize_config(t)
        for t in remote_normalized.get("data_sources", {}).get("tables", [])
    }

    for table_id in local_tables:
        if table_id not in remote_tables:
            tables_added.append(table_id)
        elif local_tables[table_id] != remote_tables[table_id]:
            tables_modified.append(table_id)

    for table_id in remote_tables:
        if table_id not in local_tables:
            tables_removed.append(table_id)

    # Check other sections (using normalized - empty/None treated as equivalent)
    local_instructions = local_normalized.get("instructions", [])
    remote_instructions = remote_normalized.get("instructions", [])
    instructions_changed = local_instructions != remote_instructions

    local_joins = local_normalized.get("joins", [])
    remote_joins = remote_normalized.get("joins", [])
    joins_changed = local_joins != remote_joins

    local_examples = local_normalized.get("example_queries", [])
    remote_examples = remote_normalized.get("example_queries", [])
    examples_changed = local_examples != remote_examples

    local_functions = local_normalized.get("functions", [])
    remote_functions = remote_normalized.get("functions", [])
    functions_changed = local_functions != remote_functions

    # Build summary
    summary_parts = []
    if tables_added:
        summary_parts.append(f"+{len(tables_added)} tables")
    if tables_removed:
        summary_parts.append(f"-{len(tables_removed)} tables")
    if tables_modified:
        summary_parts.append(f"~{len(tables_modified)} tables modified")
    if instructions_changed:
        summary_parts.append("instructions changed")
    if joins_changed:
        summary_parts.append("joins changed")
    if examples_changed:
        summary_parts.append("examples changed")
    if functions_changed:
        summary_parts.append("functions changed")

    summary = ", ".join(summary_parts) if summary_parts else "No changes"

    return DiffResult(
        has_changes=has_changes,
        changes=dict(diff) if diff else {},
        summary=summary,
        tables_added=tables_added,
        tables_removed=tables_removed,
        tables_modified=tables_modified,
        instructions_changed=instructions_changed,
        joins_changed=joins_changed,
        examples_changed=examples_changed,
        functions_changed=functions_changed,
    )


def format_diff_for_display(
    local: dict,
    remote: dict,
    diff_result: DiffResult,
) -> str:
    """Format a diff result for human-readable display.

    Args:
        local: Local configuration.
        remote: Remote configuration.
        diff_result: The computed diff result.

    Returns:
        Formatted string representation of the diff.
    """
    console = Console(record=True, force_terminal=True)

    if not diff_result.has_changes:
        console.print("[green]✓ No changes detected[/green]")
        return console.export_text()

    console.print(
        Panel(f"[bold]Changes Summary:[/bold] {diff_result.summary}", title="Diff Report")
    )

    # Tables section
    if diff_result.tables_added or diff_result.tables_removed or diff_result.tables_modified:
        table = Table(title="Table Changes")
        table.add_column("Status", style="bold")
        table.add_column("Table Identifier")

        for t in diff_result.tables_added:
            table.add_row("[green]+[/green] Added", t)
        for t in diff_result.tables_removed:
            table.add_row("[red]-[/red] Removed", t)
        for t in diff_result.tables_modified:
            table.add_row("[yellow]~[/yellow] Modified", t)

        console.print(table)

    # Other sections
    if diff_result.instructions_changed:
        console.print("[yellow]• Instructions have changed[/yellow]")
    if diff_result.joins_changed:
        console.print("[yellow]• Joins have changed[/yellow]")
    if diff_result.examples_changed:
        console.print("[yellow]• Example queries have changed[/yellow]")
    if diff_result.functions_changed:
        console.print("[yellow]• Functions have changed[/yellow]")

    # Detailed diff (JSON)
    if diff_result.changes:
        console.print("\n[bold]Detailed Changes:[/bold]")
        diff_json = json.dumps(diff_result.changes, indent=2, default=str)
        syntax = Syntax(diff_json, "json", theme="monokai", line_numbers=True)
        console.print(syntax)

    return console.export_text()


def print_diff(
    local: dict,
    remote: dict,
    diff_result: DiffResult,
) -> None:
    """Print a diff result to the console with rich formatting.

    Args:
        local: Local configuration.
        remote: Remote configuration.
        diff_result: The computed diff result.
    """
    console = Console()

    if not diff_result.has_changes:
        console.print("[green]✓ No changes detected - local matches remote[/green]")
        return

    console.print()
    console.print(
        Panel(
            Text(diff_result.summary, style="bold"),
            title="[bold blue]Space Changes Detected[/bold blue]",
            border_style="blue",
        )
    )

    # Tables section
    if diff_result.tables_added or diff_result.tables_removed or diff_result.tables_modified:
        console.print()
        table = Table(title="📊 Data Source Tables", show_header=True, header_style="bold magenta")
        table.add_column("Change", width=10)
        table.add_column("Table Identifier")

        for t in sorted(diff_result.tables_added):
            table.add_row("[green]+ ADD[/green]", t)
        for t in sorted(diff_result.tables_removed):
            table.add_row("[red]- DEL[/red]", t)
        for t in sorted(diff_result.tables_modified):
            table.add_row("[yellow]~ MOD[/yellow]", t)

        console.print(table)

    # Configuration sections
    config_changes = []
    if diff_result.instructions_changed:
        config_changes.append(("Instructions", "Natural language guidance"))
    if diff_result.joins_changed:
        config_changes.append(("Joins", "Table relationships"))
    if diff_result.examples_changed:
        config_changes.append(("Examples", "Sample queries"))
    if diff_result.functions_changed:
        config_changes.append(("Functions", "Registered UDFs"))

    if config_changes:
        console.print()
        config_table = Table(
            title="⚙️  Configuration Changes", show_header=True, header_style="bold cyan"
        )
        config_table.add_column("Section")
        config_table.add_column("Description")

        for section, desc in config_changes:
            config_table.add_row(f"[yellow]~[/yellow] {section}", desc)

        console.print(config_table)

    console.print()
