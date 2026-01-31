"""Base world class for Plato worlds."""

from __future__ import annotations

import logging
import os
import subprocess
from abc import ABC, abstractmethod
from pathlib import Path
from typing import TYPE_CHECKING, Any, ClassVar, Generic, TypeVar, get_args, get_origin

from pydantic import BaseModel, Field

from plato.worlds.config import RunConfig

if TYPE_CHECKING:
    from plato.v2.async_.environment import Environment
    from plato.v2.async_.session import Session

from plato.agents.artifacts import (
    upload_artifact as _upload_artifact_raw,
)
from plato.agents.otel import (
    get_tracer,
    init_tracing,
    shutdown_tracing,
)
from plato.agents.runner import run_agent as _run_agent_raw

logger = logging.getLogger(__name__)


def _get_plato_version() -> str:
    """Get the installed plato SDK version."""
    try:
        from importlib.metadata import version

        return version("plato")
    except Exception:
        return "unknown"


# Global registry of worlds
_WORLD_REGISTRY: dict[str, type[BaseWorld]] = {}

# Type variable for config
ConfigT = TypeVar("ConfigT", bound=RunConfig)


def register_world(name: str | None = None):
    """Decorator to register a world class.

    Usage:
        @register_world("code")
        class CodeWorld(BaseWorld[CodeWorldConfig]):
            ...
    """

    def decorator(cls: type[BaseWorld]) -> type[BaseWorld]:
        world_name = name or getattr(cls, "name", cls.__name__.lower().replace("world", ""))
        _WORLD_REGISTRY[world_name] = cls
        logger.debug(f"Registered world: {world_name} -> {cls.__name__}")
        return cls

    return decorator


def get_registered_worlds() -> dict[str, type[BaseWorld]]:
    """Get all registered worlds."""
    return _WORLD_REGISTRY.copy()


def get_world(name: str) -> type[BaseWorld] | None:
    """Get a world by name."""
    return _WORLD_REGISTRY.get(name)


class Observation(BaseModel):
    """Observation returned from reset/step."""

    data: dict[str, Any] = Field(default_factory=dict)

    model_config = {"extra": "allow"}


class StepResult(BaseModel):
    """Result of a step."""

    observation: Observation
    done: bool = False
    info: dict[str, Any] = Field(default_factory=dict)


class BaseWorld(ABC, Generic[ConfigT]):
    """Base class for Plato worlds.

    Subclass with a config type parameter for fully typed config access:

        class CodeWorldConfig(RunConfig):
            repository_url: str
            prompt: str
            coder: Annotated[AgentConfig, Agent(description="Coding agent")]
            git_token: Annotated[str | None, Secret(description="GitHub token")] = None

        @register_world("code")
        class CodeWorld(BaseWorld[CodeWorldConfig]):
            name = "code"
            description = "Run coding agents"

            async def reset(self) -> Observation:
                url = self.config.repository_url  # typed as str
                agent = self.config.coder          # typed as AgentConfig
                token = self.config.git_token      # typed as str | None
    """

    # Class attributes
    name: ClassVar[str] = "base"
    description: ClassVar[str] = ""

    # Instance attributes
    config: ConfigT  # Typed via generic parameter
    plato_session: Session | None = None  # Connected Plato session (if running on managed VM)

    def __init__(self) -> None:
        self.logger = logging.getLogger(f"plato.worlds.{self.name}")
        self._step_count: int = 0
        self.plato_session = None
        self._current_step_id: str | None = None
        self._session_id: str | None = None
        self._agent_containers: list[str] = []  # Track spawned agent containers for cleanup

    @classmethod
    def get_config_class(cls) -> type[RunConfig]:
        """Get the config class from the generic parameter."""
        # Walk up the class hierarchy to find Generic base
        for base in getattr(cls, "__orig_bases__", []):
            origin = get_origin(base)
            if origin is BaseWorld:
                args = get_args(base)
                if args and isinstance(args[0], type) and issubclass(args[0], RunConfig):
                    return args[0]
        return RunConfig

    @classmethod
    def get_version(cls) -> str:
        """Get version from package metadata."""
        import importlib.metadata

        for pkg_name in [cls.__module__.split(".")[0], f"plato-world-{cls.name}"]:
            try:
                return importlib.metadata.version(pkg_name)
            except importlib.metadata.PackageNotFoundError:
                continue
        return "0.0.0"

    @classmethod
    def get_schema(cls) -> dict:
        """Get full schema including world config, agents, secrets, and envs."""
        config_class = cls.get_config_class()
        schema = config_class.get_json_schema()

        result = {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "type": "object",
            "properties": schema.get("properties", {}),
            "required": schema.get("required", []),
            "agents": schema.get("agents", []),
            "secrets": schema.get("secrets", []),
            "envs": schema.get("envs", []),
        }

        # Include env_list if present (for worlds with arbitrary environment lists)
        if "env_list" in schema:
            result["env_list"] = schema["env_list"]

        # Include $defs if present (for nested type references)
        if "$defs" in schema:
            result["$defs"] = schema["$defs"]

        return result

    @abstractmethod
    async def reset(self) -> Observation:
        """Setup the world and return initial observation.

        Access configuration via self.config (fully typed).
        """
        pass

    @abstractmethod
    async def step(self) -> StepResult:
        """Execute one step of the world.

        Called repeatedly until done=True is returned.
        """
        pass

    async def close(self) -> None:
        """Cleanup resources. Called after run completes."""
        await self._cleanup_agent_containers()

    async def _cleanup_agent_containers(self) -> None:
        """Stop any agent containers spawned by this world."""
        import asyncio

        if not self._agent_containers:
            return

        self.logger.info(f"Stopping {len(self._agent_containers)} agent container(s)...")
        for container_name in self._agent_containers:
            try:
                proc = await asyncio.create_subprocess_exec(
                    "docker",
                    "stop",
                    container_name,
                    stdout=asyncio.subprocess.DEVNULL,
                    stderr=asyncio.subprocess.DEVNULL,
                )
                await proc.wait()
                self.logger.debug(f"Stopped container: {container_name}")
            except Exception as e:
                self.logger.warning(f"Failed to stop container {container_name}: {e}")
        self._agent_containers.clear()
        self.logger.info("Agent containers stopped")

    async def run_agent(
        self,
        image: str,
        config: dict,
        instruction: str,
        workspace: str | None = None,
        logs_dir: str | None = None,
        pull: bool = True,
    ) -> str:
        """Run an agent in a Docker container, tracking the container for cleanup.

        This is a wrapper around plato.agents.runner.run_agent that automatically
        tracks spawned containers so they can be cleaned up when the world closes.

        Args:
            image: Docker image URI
            config: Agent configuration dict
            instruction: Task instruction for the agent
            workspace: Docker volume name for workspace
            logs_dir: Ignored (kept for backwards compatibility)
            pull: Whether to pull the image first

        Returns:
            The container name that was created

        Note: Common API key environment variables (ANTHROPIC_API_KEY, etc.)
        are automatically forwarded to the agent container.
        """
        container_name = await _run_agent_raw(
            image=image,
            config=config,
            instruction=instruction,
            workspace=workspace,
            logs_dir=logs_dir,
            pull=pull,
        )
        self._agent_containers.append(container_name)
        return container_name

    async def _connect_plato_session(self) -> None:
        """Connect to Plato session from config.

        This is called automatically during run() to restore the session
        and start sending heartbeats while the world runs.
        """
        if not self.config.plato_session:
            return

        try:
            from plato.v2.async_.session import Session

            self.logger.info("Restoring Plato session from serialized data")
            self.plato_session = await Session.load(self.config.plato_session, start_heartbeat=True)
            self.logger.info(f"Plato session {self.plato_session.session_id} restored, heartbeat started")
        except Exception as e:
            self.logger.warning(f"Failed to restore Plato session: {e}")

    async def _disconnect_plato_session(self) -> None:
        """Stop heartbeat for the Plato session (does not close the session)."""
        if self.plato_session:
            try:
                await self.plato_session.stop_heartbeat()
                self.logger.info("Plato session heartbeat stopped")
            except Exception as e:
                self.logger.warning(f"Error stopping Plato heartbeat: {e}")

    async def _create_checkpoint(self) -> dict[str, str] | None:
        """Create a checkpoint snapshot of all environments (excluding configured envs).

        Uses snapshot_store for efficient chunk-based deduplication.

        Returns:
            Dict mapping environment alias to artifact_id, or None if no session connected.
        """
        if not self.plato_session:
            self.logger.warning("Cannot create checkpoint: Plato session not connected")
            return None

        exclude_envs = set(self.config.checkpoint.exclude_envs)
        envs_to_snapshot = [env for env in self.plato_session.envs if env.alias not in exclude_envs]

        if not envs_to_snapshot:
            self.logger.info("No environments to checkpoint (all excluded)")
            return {}

        self.logger.info(
            f"Creating checkpoint for {len(envs_to_snapshot)} environment(s): {[e.alias for e in envs_to_snapshot]}"
        )

        results: dict[str, str] = {}
        for env in envs_to_snapshot:
            try:
                result = await env.snapshot_store()
                artifact_id = result.artifact_id
                results[env.alias] = artifact_id

                # Check for success/error fields (available after SDK regeneration)
                success = getattr(result, "success", True)
                error = getattr(result, "error", None)

                if not success or error:
                    self.logger.error(
                        f"Checkpoint failed for '{env.alias}': {error or 'unknown error'} (job_id={env.job_id})"
                    )
                elif artifact_id:
                    self.logger.info(f"Checkpoint created for '{env.alias}': {artifact_id}")
                else:
                    self.logger.warning(
                        f"Checkpoint for '{env.alias}' returned empty artifact_id (job_id={env.job_id})"
                    )
            except Exception as e:
                self.logger.error(f"Failed to checkpoint '{env.alias}': {e}")

        return results

    def _init_state_directory(self) -> None:
        """Initialize the state directory as a git repository.

        Creates the state directory if it doesn't exist and initializes it
        as a git repository with an initial commit.
        """
        if not self.config.state.enabled:
            return

        state_path = Path(self.config.state.path)

        # Create directory if it doesn't exist
        if not state_path.exists():
            state_path.mkdir(parents=True)
            self.logger.info(f"Created state directory: {state_path}")

        # Check if already a git repo
        git_dir = state_path / ".git"
        if git_dir.exists():
            self.logger.info(f"State directory already initialized: {state_path}")
            return

        # Initialize git repo
        try:
            subprocess.run(
                ["git", "init"],
                cwd=state_path,
                capture_output=True,
                check=True,
            )
            # Create initial commit (even if empty)
            subprocess.run(
                ["git", "config", "user.email", "plato@plato.so"],
                cwd=state_path,
                capture_output=True,
                check=True,
            )
            subprocess.run(
                ["git", "config", "user.name", "Plato"],
                cwd=state_path,
                capture_output=True,
                check=True,
            )
            # Add all files and create initial commit
            subprocess.run(
                ["git", "add", "-A"],
                cwd=state_path,
                capture_output=True,
                check=True,
            )
            subprocess.run(
                ["git", "commit", "--allow-empty", "-m", "Initial state"],
                cwd=state_path,
                capture_output=True,
                check=True,
            )
            self.logger.info(f"Initialized git repo in state directory: {state_path}")
        except subprocess.CalledProcessError as e:
            self.logger.warning(f"Failed to initialize state git repo: {e.stderr}")

    def _commit_state(self, message: str) -> bool:
        """Commit current state directory changes.

        Args:
            message: Commit message

        Returns:
            True if commit was created (or no changes), False on error.
        """
        if not self.config.state.enabled:
            return True

        state_path = Path(self.config.state.path)
        if not state_path.exists():
            return True

        try:
            # Add all changes
            subprocess.run(
                ["git", "add", "-A"],
                cwd=state_path,
                capture_output=True,
                check=True,
            )
            # Check if there are changes to commit
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=state_path,
                capture_output=True,
                text=True,
                check=True,
            )
            if not result.stdout.strip():
                self.logger.debug("No state changes to commit")
                return True

            # Commit changes
            subprocess.run(
                ["git", "commit", "-m", message],
                cwd=state_path,
                capture_output=True,
                check=True,
            )
            self.logger.info(f"Committed state changes: {message}")
            return True
        except subprocess.CalledProcessError as e:
            self.logger.warning(f"Failed to commit state: {e.stderr}")
            return False

    def _create_state_bundle(self) -> bytes | None:
        """Create a git bundle of the state directory.

        Returns:
            Bundle bytes if successful, None otherwise.
        """
        if not self.config.state.enabled:
            return None

        state_path = Path(self.config.state.path)
        if not state_path.exists():
            return None

        git_dir = state_path / ".git"
        if not git_dir.exists():
            self.logger.warning("State directory is not a git repository")
            return None

        try:
            # Create bundle to stdout
            result = subprocess.run(
                ["git", "bundle", "create", "-", "--all"],
                cwd=state_path,
                capture_output=True,
                check=True,
            )
            bundle_data = result.stdout
            self.logger.info(f"Created state bundle: {len(bundle_data)} bytes")
            return bundle_data
        except subprocess.CalledProcessError as e:
            self.logger.warning(f"Failed to create state bundle: {e.stderr}")
            return None

    async def _upload_artifact(
        self,
        data: bytes,
        content_type: str = "application/octet-stream",
    ) -> bool:
        """Upload an artifact directly to S3.

        Args:
            data: Raw bytes of the artifact
            content_type: MIME type of the content

        Returns:
            True if successful, False otherwise
        """
        if not self.config.upload_url:
            self.logger.warning("Cannot upload artifact: upload_url not set")
            return False
        return await _upload_artifact_raw(
            upload_url=self.config.upload_url,
            data=data,
            content_type=content_type,
        )

    async def _create_and_upload_checkpoint(self) -> tuple[dict[str, str], bool]:
        """Create a full checkpoint including env snapshots and state bundle.

        This method:
        1. Commits any pending state changes
        2. Creates env snapshots using snapshot_store
        3. Creates and uploads state bundle to S3

        Returns:
            Tuple of (env_snapshots dict, state_bundle_uploaded bool)
        """
        # Commit state changes first
        self._commit_state(f"Checkpoint at step {self._step_count}")

        # Create env snapshots
        env_snapshots = await self._create_checkpoint()
        if env_snapshots is None:
            env_snapshots = {}

        state_bundle_uploaded = True  # Default to True if state not enabled

        # Create and upload state bundle
        if self.config.state.enabled:
            bundle_data = self._create_state_bundle()
            if bundle_data:
                success = await self._upload_artifact(
                    data=bundle_data,
                    content_type="application/octet-stream",
                )
                if success:
                    self.logger.info(f"Uploaded state bundle at step {self._step_count}")
                    state_bundle_uploaded = True
                else:
                    self.logger.warning(f"Failed to upload state bundle at step {self._step_count}")
                    state_bundle_uploaded = False

        return env_snapshots, state_bundle_uploaded

    def get_env(self, alias: str) -> Environment | None:
        """Get an environment by alias.

        Use this to access environments defined in the world config (e.g., gitea, localstack).

        Args:
            alias: The environment alias (e.g., "gitea", "localstack", "runtime")

        Returns:
            The Environment object or None if not found or session not connected.

        Example:
            gitea = self.get_env("gitea")
            if gitea:
                result = await gitea.execute("git status")
        """
        if not self.plato_session:
            self.logger.warning("Cannot get env: Plato session not connected")
            return None
        return self.plato_session.get_env(alias)

    @property
    def envs(self) -> list[Environment]:
        """Get all environments in the Plato session.

        Returns:
            List of Environment objects. Empty list if session not connected.
        """
        if not self.plato_session:
            return []
        return self.plato_session.envs

    def get_sim_env_vars(self) -> dict[str, str]:
        """Get environment variables from all configured sims.

        Automatically discovers and loads env vars from sims like localstack, gitea, etc.
        based on the environments configured in the world.

        Returns:
            Dict of environment variable name -> value

        Raises:
            ImportError: If a sim environment is configured but package is not installed.

        Example:
            env_vars = self.get_sim_env_vars()
            # Returns: {"AWS_ENDPOINT_URL": "https://...", "GITEA_URL": "https://...", ...}
        """
        env_vars: dict[str, str] = {}

        # Known sim packages and their env aliases
        sim_packages = [
            ("localstack", "localstack"),
            ("gitea", "gitea"),
        ]

        for package_name, env_alias in sim_packages:
            env = self.get_env(env_alias)
            if not env:
                continue

            try:
                # Dynamically import the sim package
                sim_module = __import__(f"plato.sims.{package_name}", fromlist=[package_name])

                # Get service URLs and env vars
                service_urls = sim_module.get_service_urls(env.job_id)
                sim_vars = sim_module.get_env_vars(service_urls)
                env_vars.update(sim_vars)
                self.logger.info(f"{package_name} env vars: {list(sim_vars.keys())}")
            except ImportError:
                raise ImportError(
                    f"Environment '{env_alias}' is configured but 'plato.sims.{package_name}' "
                    f"package is not installed.\n\n"
                    f"Install sims packages:\n"
                    f'  export INDEX_URL="https://__token__:${{PLATO_API_KEY}}@plato.so/api/v2/pypi/sims/simple/"\n'
                    f"  uv pip install '.[sims]' --extra-index-url $INDEX_URL"
                ) from None
            except Exception as e:
                self.logger.warning(f"Failed to get {package_name} env vars: {e}")

        return env_vars

    def get_sim_instructions(self) -> str:
        """Get usage instructions from all configured sims.

        Returns markdown-formatted instructions for using LocalStack, Gitea, etc.
        based on the environments configured in the world.

        Returns:
            Markdown string with instructions, or empty string if no sims configured.

        Raises:
            ImportError: If a sim environment is configured but package is not installed.

        Example:
            instructions = self.get_sim_instructions()
            # Returns markdown with LocalStack/Gitea setup instructions
        """
        instructions_parts: list[str] = []

        # Known sim packages and their env aliases
        sim_packages = [
            ("localstack", "localstack"),
            ("gitea", "gitea"),
        ]

        for package_name, env_alias in sim_packages:
            env = self.get_env(env_alias)
            if not env:
                continue

            try:
                # Dynamically import the sim package
                sim_module = __import__(f"plato.sims.{package_name}", fromlist=[package_name])

                # Get instructions using the job_id
                if hasattr(sim_module, "get_instructions_from_job"):
                    instructions = sim_module.get_instructions_from_job(env.job_id)
                    if instructions:
                        instructions_parts.append(instructions)
                        self.logger.info(f"Added {package_name} instructions to prompt")
            except ImportError:
                raise ImportError(
                    f"Environment '{env_alias}' is configured but 'plato.sims.{package_name}' "
                    f"package is not installed.\n\n"
                    f"Install sims packages:\n"
                    f'  export INDEX_URL="https://__token__:${{PLATO_API_KEY}}@plato.so/api/v2/pypi/sims/simple/"\n'
                    f"  uv pip install '.[sims]' --extra-index-url $INDEX_URL"
                ) from None
            except Exception as e:
                self.logger.warning(f"Failed to get {package_name} instructions: {e}")

        if instructions_parts:
            return "\n\n---\n\n".join(instructions_parts)
        return ""

    def format_instruction_with_sims(self, instruction: str) -> str:
        """Format an instruction with sim context prepended.

        Automatically adds available service instructions (LocalStack, Gitea, etc.)
        before the main instruction.

        Args:
            instruction: The base instruction/task

        Returns:
            Formatted instruction with sim context, or original instruction if no sims.

        Example:
            formatted = self.format_instruction_with_sims("Fix the bug in main.py")
            # Returns:
            # ## Available Services
            # The following services are available...
            # [LocalStack instructions]
            # ---
            # ## Task
            # Fix the bug in main.py
        """
        sim_instructions = self.get_sim_instructions()

        if sim_instructions:
            return f"""## Available Services

The following services are available for your use:

{sim_instructions}

---

## Task

{instruction}"""
        return instruction

    async def run(self, config: ConfigT) -> None:
        """Run the world: reset -> step until done -> close.

        This is the main entry point. If plato_session_id is provided in config,
        automatically connects to the Plato session to send heartbeats.
        """
        self.config = config
        self._step_count = 0

        self.logger.info(f"Starting world '{self.name}'")

        # Initialize state directory (creates git repo if needed)
        self._init_state_directory()

        # Initialize OTel tracing and session info for artifact uploads
        if config.session_id:
            self._session_id = config.session_id

            # Set environment variables for agent runners (which run in Docker)
            os.environ["SESSION_ID"] = config.session_id
            if config.otel_url:
                # For agents in Docker, convert localhost to host.docker.internal
                # so they can reach the host machine's Chronos instance
                agent_otel_url = config.otel_url
                if "localhost" in agent_otel_url or "127.0.0.1" in agent_otel_url:
                    agent_otel_url = agent_otel_url.replace("localhost", "host.docker.internal")
                    agent_otel_url = agent_otel_url.replace("127.0.0.1", "host.docker.internal")
                os.environ["OTEL_EXPORTER_OTLP_ENDPOINT"] = agent_otel_url
                os.environ["OTEL_EXPORTER_OTLP_PROTOCOL"] = "http/protobuf"
            if config.upload_url:
                os.environ["UPLOAD_URL"] = config.upload_url

            # Initialize OTel tracing for the world itself (runs on host, not in Docker)
            if config.otel_url:
                logger.debug(f"Initializing OTel tracing with endpoint: {config.otel_url}")
                init_tracing(
                    service_name=f"world-{self.name}",
                    session_id=config.session_id,
                    otlp_endpoint=config.otel_url,
                )
            else:
                logger.debug("No otel_url in config - OTel tracing disabled")

        # Log version info (goes to OTel after init_tracing)
        plato_version = _get_plato_version()
        world_version = self.get_version()
        self.logger.info(f"World version: {world_version}, Plato SDK version: {plato_version}")

        # Connect to Plato session if configured (for heartbeats)
        await self._connect_plato_session()

        # Get tracer for spans
        tracer = get_tracer("plato.world")

        # Create root session span that encompasses everything
        # This ensures all child spans share the same trace_id
        with tracer.start_as_current_span("session") as session_span:
            session_span.set_attribute("plato.world.name", self.name)
            session_span.set_attribute("plato.world.version", self.get_version())
            session_span.set_attribute("plato.session.id", config.session_id)

            try:
                # Execute reset with OTel span
                with tracer.start_as_current_span("reset") as reset_span:
                    obs = await self.reset()
                    obs_data = obs.model_dump() if hasattr(obs, "model_dump") else str(obs)
                    reset_span.set_attribute("plato.observation", str(obs_data)[:1000])
                self.logger.info(f"World reset complete: {obs}")

                while True:
                    self._step_count += 1

                    # Execute step with OTel span
                    with tracer.start_as_current_span(f"step_{self._step_count}") as step_span:
                        step_span.set_attribute("plato.step.number", self._step_count)

                        # Store span context for nested agent spans
                        self._current_step_id = format(step_span.get_span_context().span_id, "016x")

                        result = await self.step()

                        step_span.set_attribute("plato.step.done", result.done)
                        obs_data = (
                            result.observation.model_dump()
                            if hasattr(result.observation, "model_dump")
                            else str(result.observation)
                        )
                        step_span.set_attribute("plato.step.observation", str(obs_data)[:1000])

                    self.logger.info(f"Step {self._step_count}: done={result.done}")

                    # Create checkpoint if enabled and interval matches
                    if self.config.checkpoint.enabled and self._step_count % self.config.checkpoint.interval == 0:
                        self.logger.info(f"Creating checkpoint after step {self._step_count}")
                        with tracer.start_as_current_span("checkpoint") as checkpoint_span:
                            checkpoint_span.set_attribute("plato.checkpoint.step", self._step_count)
                            env_snapshots, state_bundle_uploaded = await self._create_and_upload_checkpoint()

                            checkpoint_span.set_attribute("plato.checkpoint.success", len(env_snapshots) > 0)
                            checkpoint_span.set_attribute(
                                "plato.checkpoint.state_bundle_uploaded", state_bundle_uploaded
                            )

                            if env_snapshots:
                                checkpoint_span.set_attribute(
                                    "plato.checkpoint.environments", list(env_snapshots.keys())
                                )
                                checkpoint_span.set_attribute(
                                    "plato.checkpoint.artifact_ids", list(env_snapshots.values())
                                )

                    if result.done:
                        break

            finally:
                await self.close()
                await self._disconnect_plato_session()

        # Shutdown OTel tracing and clear session info (outside the span)
        shutdown_tracing()
        self._session_id = None

        self.logger.info(f"World '{self.name}' completed after {self._step_count} steps")
