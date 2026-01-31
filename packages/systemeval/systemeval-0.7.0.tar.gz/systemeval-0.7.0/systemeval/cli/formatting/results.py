"""Test result display formatting for systemeval CLI."""
from typing import TYPE_CHECKING

from rich.console import Console
from rich.table import Table

if TYPE_CHECKING:
    from systemeval.types.results import TestResult

console = Console()


def display_results(results: "TestResult") -> None:
    """Display test results in a formatted table.

    Args:
        results: TestResult object with test execution results.
    """
    from systemeval.adapters import Verdict

    # Summary table
    table = Table(title="Test Results Summary")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="white")

    # Verdict first - most important
    verdict = results.verdict
    if verdict == Verdict.PASS:
        table.add_row("Verdict", "[green bold]PASS[/green bold]")
    elif verdict == Verdict.FAIL:
        table.add_row("Verdict", "[red bold]FAIL[/red bold]")
    else:
        table.add_row("Verdict", "[yellow bold]ERROR[/yellow bold]")

    table.add_row("Category", results.category or "default")
    table.add_row("Total", str(results.total))
    table.add_row("Passed", f"[green]{results.passed}[/green]")
    table.add_row("Failed", f"[red]{results.failed}[/red]" if results.failed > 0 else "0")
    table.add_row("Skipped", str(results.skipped))
    table.add_row("Errors", f"[red]{results.errors}[/red]" if results.errors > 0 else "0")

    if results.duration:
        table.add_row("Duration", f"{results.duration:.2f}s")

    if results.coverage_percent is not None:
        coverage_color = "green" if results.coverage_percent >= 80 else "yellow"
        table.add_row("Coverage", f"[{coverage_color}]{results.coverage_percent:.1f}%[/{coverage_color}]")

    table.add_row("Exit Code", str(results.exit_code))

    console.print(table)

    # Overall result banner
    if verdict == Verdict.ERROR:
        console.print(f"\n[yellow bold]======== ERROR ========[/yellow bold]")
    elif verdict == Verdict.FAIL:
        console.print(f"\n[red bold]======== FAILED ========[/red bold]")
    else:
        console.print(f"\n[green bold]======== PASSED ========[/green bold]")
