"""Docker environment management commands for systemeval CLI."""
from pathlib import Path
from typing import Optional
import sys

import click
from rich.console import Console
from rich.table import Table

console = Console()


@click.group()
def docker() -> None:
    """Docker environment management commands."""
    pass


@docker.command()
@click.option('--env', '-e', 'env_name', help='Environment name from systemeval.yaml')
@click.option('--config', type=click.Path(exists=True), help='Path to config file')
def status(env_name: Optional[str], config: Optional[str]) -> None:
    """Show Docker environment status (containers, health, ports)."""
    from systemeval.config import find_config_file, load_config
    from systemeval.utils.docker.preflight import run_preflight, check_containers_running
    from systemeval.utils.docker.discovery import find_compose_file, discover_compose_file

    config_path = Path(config) if config else find_config_file()
    if config_path:
        test_config = load_config(config_path)
        project_dir = config_path.parent
    else:
        test_config = None
        project_dir = Path.cwd()

    # Run preflight
    compose_file = None
    if test_config and env_name and env_name in (test_config.environments or {}):
        env_config = test_config.environments[env_name]
        if hasattr(env_config, 'compose_file'):
            compose_file = env_config.compose_file
        elif isinstance(env_config, dict):
            compose_file = env_config.get('compose_file')

    preflight = run_preflight(project_dir=project_dir, compose_file=compose_file)
    console.print()
    console.print("[bold]Docker Environment Status[/bold]")
    console.print()

    table = Table(show_header=True)
    table.add_column("Check", style="cyan")
    table.add_column("Status")
    table.add_column("Details", style="dim")

    for check in preflight.checks:
        status_str = "[green]PASS[/green]" if check["status"] == "pass" else (
            "[red]FAIL[/red]" if check["status"] == "fail" else "[yellow]WARN[/yellow]"
        )
        table.add_row(check["name"], status_str, check["detail"])

    console.print(table)

    # Show running containers if compose file found
    if preflight.ok:
        compose_path = find_compose_file(project_dir) if not compose_file else project_dir / compose_file
        if compose_path and compose_path.exists():
            running = check_containers_running(compose_path, project_dir)
            console.print()
            if running:
                console.print(f"[green]Running containers:[/green] {', '.join(running)}")
            else:
                console.print("[yellow]No containers currently running[/yellow]")

            # Show service info from compose file
            compose_info = discover_compose_file(project_dir)
            if compose_info:
                inferred_test = compose_info.get_test_service()
                if inferred_test:
                    port = compose_info.get_health_port(inferred_test)
                    console.print(f"[dim]Inferred test service: {inferred_test} (port {port})[/dim]")


@docker.command()
@click.option('--env', '-e', 'env_name', help='Environment name from systemeval.yaml')
@click.option('--config', type=click.Path(exists=True), help='Path to config file')
@click.option('--service', '-s', help='Service to exec into (defaults to test service)')
@click.argument('command', nargs=-1, required=True)
def exec(env_name: Optional[str], config: Optional[str], service: Optional[str], command: tuple) -> None:
    """Execute a command in a Docker test container."""
    from systemeval.config import find_config_file, load_config
    from systemeval.utils.docker import DockerResourceManager
    from systemeval.utils.docker.discovery import resolve_docker_config

    config_path = Path(config) if config else find_config_file()
    project_dir = config_path.parent if config_path else Path.cwd()

    # Resolve config
    raw_config = {"type": "docker-compose"}
    if config_path:
        test_config = load_config(config_path)
        if env_name and env_name in (test_config.environments or {}):
            env_config = test_config.environments[env_name]
            if hasattr(env_config, 'model_dump'):
                raw_config = env_config.model_dump()
            elif isinstance(env_config, dict):
                raw_config = env_config

    resolved = resolve_docker_config(raw_config, project_dir)
    target_service = service or resolved.get("test_service", "django")
    compose_file = resolved.get("compose_file", "docker-compose.yml")

    docker = DockerResourceManager(
        compose_file=compose_file,
        project_dir=str(project_dir),
    )

    cmd_str = " ".join(command)
    console.print(f"[dim]Executing in {target_service}: {cmd_str}[/dim]")
    result = docker.exec(target_service, ["sh", "-c", cmd_str], stream=True)
    sys.exit(result.exit_code)


@docker.command()
@click.option('--env', '-e', 'env_name', help='Environment name from systemeval.yaml')
@click.option('--config', type=click.Path(exists=True), help='Path to config file')
@click.option('--service', '-s', help='Service to get logs from (all if omitted)')
@click.option('--follow', '-f', is_flag=True, help='Follow log output')
@click.option('--tail', '-n', type=int, default=100, help='Number of lines to show')
def logs(env_name: Optional[str], config: Optional[str], service: Optional[str], follow: bool, tail: int) -> None:
    """View Docker container logs."""
    from systemeval.config import find_config_file, load_config
    from systemeval.utils.docker import DockerResourceManager
    from systemeval.utils.docker.discovery import resolve_docker_config

    config_path = Path(config) if config else find_config_file()
    project_dir = config_path.parent if config_path else Path.cwd()

    raw_config = {"type": "docker-compose"}
    if config_path:
        test_config = load_config(config_path)
        if env_name and env_name in (test_config.environments or {}):
            env_config = test_config.environments[env_name]
            if hasattr(env_config, 'model_dump'):
                raw_config = env_config.model_dump()
            elif isinstance(env_config, dict):
                raw_config = env_config

    resolved = resolve_docker_config(raw_config, project_dir)
    compose_file = resolved.get("compose_file", "docker-compose.yml")

    docker = DockerResourceManager(
        compose_file=compose_file,
        project_dir=str(project_dir),
    )

    result = docker.logs(service=service, tail=tail, follow=follow)
    if not follow:
        console.print(result.stdout)


@docker.command()
@click.option('--env', '-e', 'env_name', help='Environment name from systemeval.yaml')
@click.option('--config', type=click.Path(exists=True), help='Path to config file')
def ready(env_name: Optional[str], config: Optional[str]) -> None:
    """Check if Docker test environment is ready."""
    from systemeval.config import find_config_file, load_config
    from systemeval.utils.docker.preflight import run_preflight

    config_path = Path(config) if config else find_config_file()
    project_dir = config_path.parent if config_path else Path.cwd()

    # Run preflight
    compose_file = None
    if config_path:
        test_config = load_config(config_path)
        if env_name and env_name in (test_config.environments or {}):
            env_config = test_config.environments[env_name]
            if hasattr(env_config, 'compose_file'):
                compose_file = env_config.compose_file
            elif isinstance(env_config, dict):
                compose_file = env_config.get('compose_file')

    preflight = run_preflight(project_dir=project_dir, compose_file=compose_file)

    if preflight.ok:
        console.print("[green]✓ Docker environment is ready[/green]")
        sys.exit(0)
    else:
        console.print("[red]✗ Docker environment not ready[/red]")
        for check in preflight.checks:
            if check["status"] in ("fail", "warn"):
                console.print(f"  [yellow]→[/yellow] {check['name']}: {check['detail']}")
        sys.exit(1)
