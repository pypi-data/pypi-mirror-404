"""
Docker Compose environment for multi-container testing.

Uses DockerResourceManager for container lifecycle management.
Supports flexible test execution including custom scripts.

Modes:
- Full lifecycle: build → up → health check → test → teardown
- Attach mode: exec into already-running containers (attach: true)
- Auto-discovery: omit config fields and let them be inferred from compose file
"""
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from systemeval.types import TestResult
from systemeval.environments.base import Environment, EnvironmentType, SetupResult
from systemeval.environments.executor import DockerExecutor
from systemeval.utils.docker import (
    DockerResourceManager,
    HealthCheckConfig,
)
from systemeval.utils.docker.discovery import resolve_docker_config, validate_docker_config
from systemeval.utils.docker.preflight import run_preflight
from systemeval.utils.commands import build_test_command
from systemeval.utils.logging import get_logger

logger = get_logger(__name__)


class DockerComposeEnvironment(Environment):
    """
    Environment for Docker Compose-based testing.

    Supports three usage patterns:

    1. Minimal config (auto-discovery):
       environments:
         backend:
           type: docker-compose

    2. Attach to running containers:
       environments:
         backend:
           type: docker-compose
           attach: true

    3. Full explicit config (backward compatible):
       environments:
         backend:
           type: docker-compose
           compose_file: local.yml
           services: [django, postgres, redis]
           test_service: django
           ...
    """

    def __init__(self, name: str, config: Dict[str, Any]) -> None:
        super().__init__(name, config)

        self.attach = config.get("attach", False)
        auto_discover = config.get("auto_discover", True)

        # Resolve project directory for file discovery
        working_dir_raw = config.get("working_dir", ".")
        self._project_dir = Path(working_dir_raw).resolve() if working_dir_raw != "." else Path.cwd()

        # Auto-discover missing config from compose file
        if auto_discover:
            resolved = resolve_docker_config(config, self._project_dir)
        else:
            resolved = config

        # Extract resolved config
        self.compose_file = resolved.get("compose_file") or "docker-compose.yml"
        self.services = resolved.get("services", [])
        self.test_service = resolved.get("test_service") or "django"
        self.test_command = resolved.get("test_command") or "pytest"
        self.working_dir = Path(resolved.get("working_dir", "."))
        self.skip_build = resolved.get("skip_build", False)
        self.project_name = resolved.get("project_name")

        # Health check config
        health_config = resolved.get("health_check", {})
        if health_config:
            self.health_config = HealthCheckConfig(
                service=health_config.get("service", self.test_service),
                endpoint=health_config.get("endpoint", "/health/"),
                port=health_config.get("port", 8000),
                timeout=health_config.get("timeout", 120),
            )
        else:
            self.health_config = HealthCheckConfig(
                service=self.test_service,
                endpoint="/health/",
                port=8000,
                timeout=120,
            )

        # Remote Docker host config
        docker_config = resolved.get("docker", {})
        self._docker_host = None
        self._docker_context = None
        if docker_config:
            self._docker_host = docker_config.get("host")
            self._docker_context = docker_config.get("context")

        # Initialize Docker manager
        self.docker = DockerResourceManager(
            compose_file=self.compose_file,
            project_dir=str(self.working_dir),
            project_name=self.project_name,
            docker_host=self._docker_host,
            docker_context=self._docker_context,
        )

        self._is_up = False

    @property
    def env_type(self) -> EnvironmentType:
        return EnvironmentType.DOCKER_COMPOSE

    def _run_preflight(self) -> SetupResult:
        """Run pre-flight checks and return SetupResult if they fail."""
        preflight = run_preflight(
            project_dir=self._project_dir,
            compose_file=self.compose_file,
            services=self.services or None,
            test_service=self.test_service,
            attach=self.attach,
        )

        if not preflight.ok:
            error_msg = "\n".join(preflight.errors)
            return SetupResult(
                success=False,
                message=f"Pre-flight checks failed:\n{error_msg}",
                duration=0.0,
                details={"preflight": [c for c in preflight.checks]},
            )
        return None

    def setup(self) -> SetupResult:
        """Build and start Docker containers, or attach to running ones."""
        logger.debug(f"Setting up Docker Compose environment: {self.name}")

        # Validate config
        errors = validate_docker_config(self.config, self._project_dir)
        if errors:
            for err in errors:
                logger.warning(f"Config validation: {err}")

        # Run pre-flight checks
        preflight_fail = self._run_preflight()
        if preflight_fail:
            return preflight_fail

        total_start = time.time()
        details: Dict[str, Any] = {}

        # Attach mode: skip lifecycle, just verify containers are running
        if self.attach:
            logger.debug("Attach mode: connecting to running containers")
            self._is_up = True
            return SetupResult(
                success=True,
                message=f"Attached to running containers (test_service: {self.test_service})",
                duration=time.time() - total_start,
                details={"mode": "attach"},
            )

        # Install signal handlers for clean shutdown
        self.docker.install_signal_handlers(self._cleanup)

        # Build phase
        if not self.skip_build:
            logger.debug("Building Docker images...")
            build_start = time.time()
            build_result = self.docker.build(
                services=self.services if self.services else None,
                stream=True,
            )
            self.timings.build = time.time() - build_start
            details["build"] = {
                "success": build_result.success,
                "duration": build_result.duration,
            }

            if not build_result.success:
                logger.error(f"Docker build failed: {build_result.error}")
                return SetupResult(
                    success=False,
                    message=f"Build failed: {build_result.error}",
                    duration=time.time() - total_start,
                    details=details,
                )

        # Start containers
        logger.debug(f"Starting Docker containers (services: {self.services or 'all'})...")
        startup_start = time.time()
        up_result = self.docker.up(
            services=self.services if self.services else None,
            detach=True,
            build=False,  # Already built
        )
        self.timings.startup = time.time() - startup_start
        details["startup"] = {
            "success": up_result.success,
            "duration": up_result.duration,
        }

        if not up_result.success:
            logger.error(f"Failed to start containers: {up_result.stderr}")
            return SetupResult(
                success=False,
                message=f"Failed to start containers: {up_result.stderr}",
                duration=time.time() - total_start,
                details=details,
            )

        self._is_up = True
        logger.debug(f"Docker containers started successfully in {time.time() - total_start:.1f}s")

        return SetupResult(
            success=True,
            message=f"Started {len(self.services) or 'all'} services",
            duration=time.time() - total_start,
            details=details,
        )

    def is_ready(self) -> bool:
        """Check if containers are healthy."""
        if not self._is_up:
            return False
        return self.docker.is_healthy(self.health_config.service)

    def wait_ready(self, timeout: int = 120) -> bool:
        """Wait for health check endpoint."""
        if not self._is_up:
            return False

        start = time.time()
        config = HealthCheckConfig(
            service=self.health_config.service,
            endpoint=self.health_config.endpoint,
            port=self.health_config.port,
            timeout=timeout,
        )

        def on_progress(msg: str) -> None:
            print(f"  {msg}")

        result = self.docker.wait_healthy(config, on_progress=on_progress)
        self.timings.health_check = time.time() - start

        return result

    def run_tests(
        self,
        suite: Optional[str] = None,
        category: Optional[str] = None,
        verbose: bool = False,
    ) -> TestResult:
        """
        Run tests inside the test service container.

        Supports:
        - Simple commands: "pytest -v"
        - Shell scripts: "./scripts/run-e2e.sh"
        - Multi-step: ["npm run build", "npm test"]
        - Complex pipelines: "cd app && ./run-tests.sh"
        """
        if not self._is_up:
            return TestResult(
                passed=0,
                failed=0,
                errors=1,
                skipped=0,
                duration=0.0,
                exit_code=2,
            )

        start = time.time()

        # Create Docker executor
        executor = DockerExecutor(
            container=self.test_service,
            compose_file=self.compose_file,
            project_dir=str(self.working_dir),
            project_name=self.project_name,
            verbose=verbose,
        )

        # Build test command with optional filters
        command = self._build_test_command(suite, category, verbose)

        # Execute tests
        result = executor.execute(
            command=command,
            timeout=self.config.get("test_timeout"),
            env=self.config.get("test_env", self.config.get("env", {})),
            stream=True,
        )

        self.timings.tests = time.time() - start

        # Parse output to extract test counts
        return executor.parse_test_results(result.stdout, result.exit_code)

    def _build_test_command(
        self,
        suite: Optional[str],
        category: Optional[str],
        verbose: bool,
    ) -> Union[str, List[str]]:
        """Build the test command with optional filters."""
        return build_test_command(self.test_command, suite, category, verbose)

    def _cleanup(self) -> None:
        """Internal cleanup for signal handlers."""
        if self._is_up and not self.attach:
            self.docker.down()
            self._is_up = False

    def teardown(self, keep_running: bool = False) -> None:
        """Stop and remove containers (skipped in attach mode)."""
        logger.debug(f"Tearing down Docker Compose environment (keep_running={keep_running})")
        start = time.time()

        # In attach mode, never tear down containers we didn't start
        if self.attach:
            logger.debug("Attach mode: skipping teardown (containers were not managed by systemeval)")
            self._is_up = False
            self.timings.cleanup = time.time() - start
            return

        if self._is_up and not keep_running:
            self.docker.down()
            self._is_up = False
            logger.debug(f"Docker containers stopped in {time.time() - start:.1f}s")

        self.docker.restore_signal_handlers()
        self.timings.cleanup = time.time() - start
