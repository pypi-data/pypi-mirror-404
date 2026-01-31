"""Docker utility modules for systemeval.

This module provides Docker-related utilities including:
- Environment detection (is_docker_environment, get_environment_type)
- Container management (get_container_id, get_docker_compose_service)
- Resource management (DockerResourceManager)
- Compose file parsing (parse_compose_file, ComposeFileInfo)
- Auto-discovery (discover_compose_file, resolve_docker_config)
- Pre-flight checks (run_preflight, PreflightResult)

Note: This was previously located in systemeval.plugins.docker but moved here
because it's not a plugin system - these are core Docker utilities.
"""

from .docker import (
    check_docker_available,
    get_container_id,
    get_docker_compose_service,
    get_environment_type,
    is_docker_environment,
)
from .docker_manager import (
    BuildResult,
    CommandResult,
    DockerResourceManager,
    HealthCheckConfig,
)
from .compose_parser import (
    ComposeFileInfo,
    ServiceInfo,
    parse_compose_file,
)
from .discovery import (
    discover_compose_file,
    find_compose_file,
    resolve_docker_config,
    validate_docker_config,
)
from .preflight import (
    PreflightResult,
    run_preflight,
)

__all__ = [
    # Environment detection
    "check_docker_available",
    "get_environment_type",
    "is_docker_environment",
    "get_container_id",
    "get_docker_compose_service",
    # Resource management
    "BuildResult",
    "CommandResult",
    "DockerResourceManager",
    "HealthCheckConfig",
    # Compose file parsing
    "ComposeFileInfo",
    "ServiceInfo",
    "parse_compose_file",
    # Auto-discovery
    "discover_compose_file",
    "find_compose_file",
    "resolve_docker_config",
    "validate_docker_config",
    # Pre-flight checks
    "PreflightResult",
    "run_preflight",
]
