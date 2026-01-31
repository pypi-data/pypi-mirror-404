"""
SystemEval CLI - Unified test runner with framework-agnostic adapters.
"""
import click

from systemeval.cli.commands import (
    register_config_commands,
    register_list_commands,
    e2e,
    test,
    docker,
)

@click.group()
@click.version_option(version=None, package_name="systemeval")
def main() -> None:
    """SystemEval - Unified test runner CLI."""
    pass


# Register modular command groups
register_config_commands(main)
register_list_commands(main)
main.add_command(e2e)
main.add_command(test)
main.add_command(docker)




if __name__ == '__main__':
    main()
