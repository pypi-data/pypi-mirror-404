"""CLI command modules for SystemEval.

This package contains modular command implementations for the SystemEval CLI.
Commands are organized by functionality:

- config_commands: Configuration management (init, validate, discover)
- list_commands: Listing available items (categories, environments, adapters, templates)
- e2e_commands: E2E test generation commands (run, status, download, init)
- test_commands: Test execution commands (test)
- docker_commands: Docker environment management (status, exec, logs, ready)

Each module provides a registration function that attaches commands to the
main CLI group.
"""

from .config_commands import register_config_commands
from .list_commands import register_list_commands
from .e2e_commands import e2e
from .test_commands import test
from .docker_commands import docker

__all__ = [
    "register_config_commands",
    "register_list_commands",
    "e2e",
    "test",
    "docker",
]
