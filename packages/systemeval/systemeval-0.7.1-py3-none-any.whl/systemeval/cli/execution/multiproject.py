"""Multi-project test execution for systemeval CLI."""
import json
import os
import subprocess
import time
from typing import TYPE_CHECKING

from rich.console import Console
from rich.table import Table

from systemeval.adapters import get_adapter
from systemeval.config import get_subproject_absolute_path
from systemeval.types.adapters import AdapterConfig

if TYPE_CHECKING:
    from systemeval.config import SystemEvalConfig, SubprojectConfig, SubprojectResult, MultiProjectResult
    from systemeval.types.options import TestCommandOptions

console = Console()


def run_single_subproject(
    root_config: "SystemEvalConfig",
    subproject: "SubprojectConfig",
    opts: "TestCommandOptions",
) -> "SubprojectResult":
    """Run tests for a single subproject.

    Args:
        root_config: Root SystemEval configuration.
        subproject: The subproject configuration to run.
        opts: Grouped CLI options.

    Returns:
        SubprojectResult with test results for this subproject.
    """
    from systemeval.config import SubprojectResult

    verbose = opts.execution.verbose
    json_output = opts.output.json_output
    failfast = opts.execution.failfast
    parallel = opts.execution.parallel
    coverage = opts.execution.coverage

    sp_path = get_subproject_absolute_path(root_config, subproject)

    if not json_output:
        console.print(f"[bold]▶ {subproject.name}[/bold] ({subproject.adapter})")

    # Check if subproject path exists
    if not sp_path.exists():
        if not json_output:
            console.print(f"  [red]✗ Path not found: {sp_path}[/red]")
        return SubprojectResult(
            name=subproject.name,
            adapter=subproject.adapter,
            status="ERROR",
            error_message=f"Subproject path not found: {sp_path}",
        )

    # Run pre_commands if defined
    if subproject.pre_commands:
        for cmd in subproject.pre_commands:
            if verbose and not json_output:
                console.print(f"  [dim]Running: {cmd}[/dim]")
            try:
                subprocess.run(
                    cmd,
                    shell=True,
                    cwd=str(sp_path),
                    check=True,
                    capture_output=not verbose,
                    env={**os.environ, **subproject.env},
                )
            except subprocess.CalledProcessError as e:
                if not json_output:
                    console.print(f"  [red]✗ Pre-command failed: {cmd}[/red]")
                return SubprojectResult(
                    name=subproject.name,
                    adapter=subproject.adapter,
                    status="ERROR",
                    error_message=f"Pre-command failed: {cmd}",
                )

    # Get adapter for this subproject
    try:
        # Create adapter config with subproject settings
        adapter_config = AdapterConfig(
            project_root=str(sp_path),
            test_directory=subproject.test_directory,
            parallel=parallel,
            coverage=coverage,
            timeout=root_config.get_effective_timeout(subproject),
            extra={
                "config_file": subproject.config_file,
                **subproject.options,
            },
        )

        # Get adapter - handle special cases
        adapter_name = subproject.adapter
        if adapter_name == "pytest-django":
            adapter_name = "pytest"  # pytest-django uses pytest adapter with Django settings

        adapter = get_adapter(adapter_name, str(sp_path))

    except (KeyError, ValueError) as e:
        if not json_output:
            console.print(f"  [red]✗ Adapter error: {e}[/red]")
        return SubprojectResult(
            name=subproject.name,
            adapter=subproject.adapter,
            status="ERROR",
            error_message=f"Adapter error: {e}",
        )

    # Set up environment variables
    env_backup = {}
    for key, value in subproject.env.items():
        env_backup[key] = os.environ.get(key)
        os.environ[key] = value

    try:
        # Run tests
        start_time = time.time()
        test_result = adapter.execute(
            tests=None,
            parallel=parallel,
            coverage=coverage,
            failfast=failfast,
            verbose=verbose,
        )
        duration = time.time() - start_time

        # Convert TestResult to SubprojectResult
        sp_result = SubprojectResult(
            name=subproject.name,
            adapter=subproject.adapter,
            passed=test_result.passed,
            failed=test_result.failed,
            errors=test_result.errors,
            skipped=test_result.skipped,
            duration=duration,
            status="PASS" if test_result.verdict.value == "PASS" else (
                "ERROR" if test_result.verdict.value == "ERROR" else "FAIL"
            ),
            failures=[
                {
                    "test": f.test_id,
                    "name": f.test_name,
                    "message": f.message,
                }
                for f in test_result.failures
            ],
        )

        # Display result
        if not json_output:
            status_icon = "✓" if sp_result.status == "PASS" else "✗"
            status_color = "green" if sp_result.status == "PASS" else "red"
            console.print(
                f"  [{status_color}]{status_icon}[/{status_color}] "
                f"{sp_result.passed} passed, {sp_result.failed} failed "
                f"({sp_result.duration:.1f}s)"
            )

        return sp_result

    except Exception as e:
        if not json_output:
            console.print(f"  [red]✗ Execution error: {e}[/red]")
        return SubprojectResult(
            name=subproject.name,
            adapter=subproject.adapter,
            status="ERROR",
            error_message=str(e),
        )

    finally:
        # Restore environment variables
        for key, value in env_backup.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


def output_multi_project_results(
    result: "MultiProjectResult",
    opts: "TestCommandOptions",
) -> None:
    """Output multi-project results in the appropriate format.

    Args:
        result: Aggregated multi-project results.
        opts: CLI options including output format.
    """
    json_output = opts.output.json_output
    template = opts.output.template

    if json_output:
        # Output JSON for CI
        console.print(json.dumps(result.to_json_dict(), indent=2))
    elif template:
        # Template output - could be extended for multi-project templates
        console.print(f"[yellow]Template output not yet implemented for multi-project mode[/yellow]")
        display_multi_project_table(result)
    else:
        # Default: Rich table output
        display_multi_project_table(result)


def display_multi_project_table(result: "MultiProjectResult") -> None:
    """Display multi-project results as a Rich table.

    Args:
        result: Aggregated multi-project results.
    """
    console.print()

    # Create table
    table = Table(title="Multi-Project Test Results", show_header=True, header_style="bold")
    table.add_column("Subproject", style="cyan")
    table.add_column("Adapter", style="dim")
    table.add_column("Passed", justify="right", style="green")
    table.add_column("Failed", justify="right", style="red")
    table.add_column("Status", justify="center")

    for sp in result.subprojects:
        status_style = "green" if sp.status == "PASS" else ("yellow" if sp.status == "SKIP" else "red")
        table.add_row(
            sp.name,
            sp.adapter,
            str(sp.passed) if sp.status != "SKIP" else "--",
            str(sp.failed) if sp.status != "SKIP" else "--",
            f"[{status_style}]{sp.status}[/{status_style}]",
        )

    # Add totals row
    table.add_section()
    verdict_style = "green" if result.verdict == "PASS" else "red"
    table.add_row(
        "[bold]TOTAL[/bold]",
        "",
        f"[bold]{result.total_passed}[/bold]",
        f"[bold]{result.total_failed}[/bold]",
        f"[bold {verdict_style}]{result.verdict}[/bold {verdict_style}]",
    )

    console.print(table)
    console.print()
