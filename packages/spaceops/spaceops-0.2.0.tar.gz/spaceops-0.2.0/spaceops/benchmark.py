"""Benchmark runner for testing Genie space accuracy."""

from __future__ import annotations

import re
import time
from pathlib import Path
from typing import Any

import yaml
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from .client import GenieAPIError, GenieClient
from .models import BenchmarkQuery, BenchmarkResult, BenchmarkSuite, BenchmarkSuiteResult


def load_benchmark_suite(path: Path | str) -> BenchmarkSuite:
    """Load a benchmark suite from a YAML file.

    Args:
        path: Path to the benchmark YAML file.

    Returns:
        BenchmarkSuite object.
    """
    path = Path(path)
    with open(path) as f:
        data = yaml.safe_load(f)

    return BenchmarkSuite(**data)


def extract_tables_from_sql(sql: str) -> list[str]:
    """Extract table names from a SQL query.

    Args:
        sql: SQL query string.

    Returns:
        List of table identifiers found in the query.
    """
    # Match patterns like: FROM catalog.schema.table, JOIN catalog.schema.table
    pattern = r"(?:FROM|JOIN)\s+([a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*){0,2})"
    matches = re.findall(pattern, sql, re.IGNORECASE)
    return [m.lower() for m in matches]


def extract_columns_from_sql(sql: str) -> list[str]:
    """Extract column names from a SQL query (SELECT clause).

    Args:
        sql: SQL query string.

    Returns:
        List of column names found in the query.
    """
    # Simplified extraction - get columns from SELECT clause
    select_match = re.search(r"SELECT\s+(.*?)\s+FROM", sql, re.IGNORECASE | re.DOTALL)
    if not select_match:
        return []

    select_clause = select_match.group(1)

    # Handle aliases and functions
    columns = []
    for part in select_clause.split(","):
        part = part.strip()
        # Skip *
        if part == "*":
            continue
        # Handle aliases: column AS alias -> take column
        if " AS " in part.upper():
            part = part.split()[0]
        # Handle table.column -> take column
        if "." in part:
            part = part.split(".")[-1]
        # Handle functions: SUM(column) -> take column
        func_match = re.search(r"\w+\(([^)]+)\)", part)
        if func_match:
            part = func_match.group(1).strip()
            if "." in part:
                part = part.split(".")[-1]

        if part and part.isidentifier():
            columns.append(part.lower())

    return columns


def evaluate_benchmark_query(
    client: GenieClient,
    space_id: str,
    query: BenchmarkQuery,
    timeout: float = 30.0,
) -> BenchmarkResult:
    """Evaluate a single benchmark query against a Genie space.

    Args:
        client: Genie API client.
        space_id: ID of the space to test.
        query: Benchmark query to evaluate.
        timeout: Maximum time to wait for response.

    Returns:
        BenchmarkResult with pass/fail status and details.
    """
    details: dict[str, Any] = {}

    try:
        # Start a conversation
        conversation_id = client.start_conversation(space_id)

        # Send the question
        response = client.send_message(space_id, conversation_id, query.question)
        message_id = response.get("id") or response.get("message_id")

        # Poll for completion
        start_time = time.time()
        sql = None

        while time.time() - start_time < timeout:
            msg = client.get_message(space_id, conversation_id, message_id)
            status = msg.get("status", "")

            if status in ("COMPLETED", "completed"):
                # Extract SQL from response
                attachments = msg.get("attachments", [])
                for att in attachments:
                    if att.get("query"):
                        sql = att["query"].get("query")
                        break
                break
            elif status in ("FAILED", "failed", "ERROR", "error"):
                return BenchmarkResult(
                    question=query.question,
                    passed=False,
                    error=msg.get("error", "Query failed"),
                    details={"status": status, "response": msg},
                )

            time.sleep(1)

        if sql is None:
            return BenchmarkResult(
                question=query.question,
                passed=False,
                error="No SQL generated or timeout",
                details={"response": msg if "msg" in dir() else None},
            )

        details["generated_sql"] = sql

        # Evaluate the SQL
        passed = True
        failure_reasons = []

        # Check expected tables
        if query.expected_tables:
            actual_tables = extract_tables_from_sql(sql)
            details["actual_tables"] = actual_tables

            for expected in query.expected_tables:
                if expected.lower() not in [t.lower() for t in actual_tables]:
                    passed = False
                    failure_reasons.append(f"Missing table: {expected}")

        # Check expected columns
        if query.expected_columns:
            actual_columns = extract_columns_from_sql(sql)
            details["actual_columns"] = actual_columns

            for expected in query.expected_columns:
                found = any(expected.lower() in c.lower() for c in actual_columns)
                if not found and expected.lower() in sql.lower():
                    found = True  # Column might be in WHERE clause etc.
                if not found:
                    passed = False
                    failure_reasons.append(f"Missing column: {expected}")

        # Check SQL contains patterns
        if query.expected_sql_contains:
            for pattern in query.expected_sql_contains:
                if pattern.lower() not in sql.lower():
                    passed = False
                    failure_reasons.append(f"Missing pattern: {pattern}")

        # Check SQL regex pattern
        if query.expected_sql_pattern and not re.search(
            query.expected_sql_pattern, sql, re.IGNORECASE
        ):
            passed = False
            failure_reasons.append(f"SQL doesn't match pattern: {query.expected_sql_pattern}")

        if failure_reasons:
            details["failure_reasons"] = failure_reasons

        return BenchmarkResult(
            question=query.question,
            passed=passed,
            actual_sql=sql,
            details=details,
        )

    except GenieAPIError as e:
        return BenchmarkResult(
            question=query.question,
            passed=False,
            error=str(e),
            details={"api_error": e.response},
        )
    except Exception as e:
        return BenchmarkResult(
            question=query.question,
            passed=False,
            error=str(e),
        )


def run_benchmark_suite(
    client: GenieClient,
    space_id: str,
    suite: BenchmarkSuite,
    verbose: bool = False,
) -> BenchmarkSuiteResult:
    """Run a complete benchmark suite against a Genie space.

    Args:
        client: Genie API client.
        space_id: ID of the space to test.
        suite: Benchmark suite to run.
        verbose: Whether to print progress.

    Returns:
        BenchmarkSuiteResult with aggregate statistics.
    """
    console = Console()
    results: list[BenchmarkResult] = []

    if verbose:
        console.print(
            Panel(
                f"[bold]Running benchmark suite:[/bold] {suite.name}\n"
                f"[dim]{suite.description or 'No description'}[/dim]\n"
                f"Queries: {len(suite.queries)} | Min accuracy: {suite.min_accuracy:.0%}",
                title="🧪 Benchmark",
            )
        )

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console if verbose else Console(quiet=True),
    ) as progress:
        task = progress.add_task("Running benchmarks...", total=len(suite.queries))

        for query in suite.queries:
            progress.update(task, description=f"Testing: {query.question[:50]}...")
            result = evaluate_benchmark_query(client, space_id, query)
            results.append(result)
            progress.advance(task)

    passed = sum(1 for r in results if r.passed)
    failed = len(results) - passed
    accuracy = passed / len(results) if results else 0.0

    suite_result = BenchmarkSuiteResult(
        suite_name=suite.name,
        total=len(results),
        passed=passed,
        failed=failed,
        accuracy=accuracy,
        results=results,
    )

    if verbose:
        print_benchmark_results(suite_result, suite.min_accuracy)

    return suite_result


def print_benchmark_results(
    result: BenchmarkSuiteResult,
    min_accuracy: float = 0.8,
) -> None:
    """Print benchmark results with rich formatting.

    Args:
        result: Benchmark suite result.
        min_accuracy: Minimum required accuracy threshold.
    """
    console = Console()

    # Summary
    status_color = "green" if result.accuracy >= min_accuracy else "red"
    status_icon = "✓" if result.accuracy >= min_accuracy else "✗"

    console.print()
    console.print(
        Panel(
            f"[bold]Accuracy:[/bold] [{status_color}]{result.accuracy:.1%}[/{status_color}] "
            f"(threshold: {min_accuracy:.0%})\n"
            f"[green]Passed:[/green] {result.passed} | [red]Failed:[/red] {result.failed} | "
            f"Total: {result.total}",
            title=f"[{status_color}]{status_icon} Benchmark Results: {result.suite_name}[/{status_color}]",
            border_style=status_color,
        )
    )

    # Detailed results table
    if result.failed > 0:
        console.print()
        table = Table(title="❌ Failed Queries", show_header=True, header_style="bold red")
        table.add_column("Question", max_width=50)
        table.add_column("Error / Reason")

        for r in result.results:
            if not r.passed:
                error = r.error or ", ".join(r.details.get("failure_reasons", ["Unknown"]))
                table.add_row(r.question[:50], error[:60])

        console.print(table)

    # All results if verbose
    console.print()
    all_table = Table(title="📋 All Results", show_header=True)
    all_table.add_column("Status", width=8)
    all_table.add_column("Question")

    for r in result.results:
        status = "[green]PASS[/green]" if r.passed else "[red]FAIL[/red]"
        all_table.add_row(status, r.question[:70])

    console.print(all_table)
    console.print()


def generate_benchmark_report(
    results: list[BenchmarkSuiteResult],
    output_format: str = "markdown",
) -> str:
    """Generate a report from multiple benchmark suite results.

    Args:
        results: List of benchmark suite results.
        output_format: Output format ('markdown' or 'json').

    Returns:
        Formatted report string.
    """
    if output_format == "json":
        import json

        return json.dumps(
            [r.model_dump() for r in results],
            indent=2,
            default=str,
        )

    # Markdown format
    lines = [
        "# Genie Space Benchmark Report",
        "",
        "## Summary",
        "",
        "| Suite | Passed | Failed | Accuracy | Status |",
        "|-------|--------|--------|----------|--------|",
    ]

    all_passed = True
    for r in results:
        status = "✅ PASS" if r.accuracy >= 0.8 else "❌ FAIL"
        if r.accuracy < 0.8:
            all_passed = False
        lines.append(f"| {r.suite_name} | {r.passed} | {r.failed} | {r.accuracy:.1%} | {status} |")

    lines.extend(
        [
            "",
            f"## Overall Status: {'✅ All benchmarks passed' if all_passed else '❌ Some benchmarks failed'}",
            "",
        ]
    )

    # Detailed failures
    for r in results:
        failed = [q for q in r.results if not q.passed]
        if failed:
            lines.extend(
                [
                    f"### Failed Queries in {r.suite_name}",
                    "",
                ]
            )
            for f in failed:
                lines.append(f"- **{f.question}**")
                if f.error:
                    lines.append(f"  - Error: {f.error}")
                if f.details.get("failure_reasons"):
                    for reason in f.details["failure_reasons"]:
                        lines.append(f"  - {reason}")
            lines.append("")

    return "\n".join(lines)
