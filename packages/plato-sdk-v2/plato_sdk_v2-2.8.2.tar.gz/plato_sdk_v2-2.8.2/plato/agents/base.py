"""Base agent class and registry for Plato agents."""

from __future__ import annotations

import json
import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, ClassVar, Generic, TypeVar, get_args, get_origin

from plato.agents.config import AgentConfig

logger = logging.getLogger(__name__)

# Global registry of agents
_AGENT_REGISTRY: dict[str, type[BaseAgent]] = {}

# Type variable for config
ConfigT = TypeVar("ConfigT", bound=AgentConfig)


def register_agent(name: str | None = None):
    """Decorator to register an agent class.

    Usage:
        @register_agent("openhands")
        class OpenHandsAgent(BaseAgent[OpenHandsConfig]):
            ...
    """

    def decorator(cls: type[BaseAgent]) -> type[BaseAgent]:
        agent_name = name or getattr(cls, "name", cls.__name__.lower().replace("agent", ""))
        _AGENT_REGISTRY[agent_name] = cls
        logger.debug(f"Registered agent: {agent_name} -> {cls.__name__}")
        return cls

    return decorator


def get_registered_agents() -> dict[str, type[BaseAgent]]:
    """Get all registered agents."""
    return _AGENT_REGISTRY.copy()


def get_agent(name: str) -> type[BaseAgent] | None:
    """Get an agent by name."""
    return _AGENT_REGISTRY.get(name)


class BaseAgent(ABC, Generic[ConfigT]):
    """Base class for Plato agents.

    Subclass with a config type parameter for fully typed config access:

        class OpenHandsConfig(AgentConfig):
            model_name: str = "anthropic/claude-sonnet-4"
            anthropic_api_key: Annotated[str | None, Secret(description="API key")] = None

        @register_agent("openhands")
        class OpenHandsAgent(BaseAgent[OpenHandsConfig]):
            name = "openhands"
            description = "OpenHands AI software engineer"

            async def run(self, instruction: str) -> None:
                # self.config is typed as OpenHandsConfig
                model = self.config.model_name
                ...
    """

    # Class attributes
    name: ClassVar[str] = "base"
    description: ClassVar[str] = ""

    # Instance attributes
    config: ConfigT

    def __init__(self) -> None:
        self.logger = logging.getLogger(f"plato.agents.{self.name}")

    @classmethod
    def get_config_class(cls) -> type[AgentConfig]:
        """Get the config class from the generic parameter."""
        for base in getattr(cls, "__orig_bases__", []):
            origin = get_origin(base)
            if origin is BaseAgent:
                args = get_args(base)
                if args and isinstance(args[0], type) and issubclass(args[0], AgentConfig):
                    return args[0]
        return AgentConfig

    @classmethod
    def get_version(cls) -> str:
        """Get version from package metadata."""
        import importlib.metadata

        for pkg_name in [cls.__module__.split(".")[0], f"plato-agent-{cls.name}"]:
            try:
                return importlib.metadata.version(pkg_name)
            except importlib.metadata.PackageNotFoundError:
                continue
        return "0.0.0"

    @classmethod
    def get_schema(cls) -> dict:
        """Get full schema for the agent including config and build schemas."""
        from plato.agents.build import BuildConfig

        config_class = cls.get_config_class()
        return {
            "config": config_class.get_json_schema(),
            "build": BuildConfig.get_json_schema(),
        }

    @abstractmethod
    async def run(self, instruction: str) -> None:
        """Run the agent with the given instruction.

        This is the main entry point for agent execution. Implementations should:
        1. Set up the environment using self.config
        2. Execute the agent's core logic
        3. Write trajectory to logs_dir if applicable

        Args:
            instruction: The task instruction/prompt for the agent.

        Raises:
            RuntimeError: If agent execution fails.
        """
        pass

    async def write_trajectory(self, trajectory: dict[str, Any]) -> None:
        """Write ATIF trajectory to the logs directory.

        Args:
            trajectory: ATIF-formatted trajectory dictionary.
        """
        logs_dir = Path(self.config.logs_dir)
        agent_logs = logs_dir / "agent"
        agent_logs.mkdir(parents=True, exist_ok=True)

        trajectory_path = agent_logs / "trajectory.json"
        with open(trajectory_path, "w") as f:
            json.dump(trajectory, f, indent=2)

        self.logger.info(f"Wrote trajectory to {trajectory_path}")
