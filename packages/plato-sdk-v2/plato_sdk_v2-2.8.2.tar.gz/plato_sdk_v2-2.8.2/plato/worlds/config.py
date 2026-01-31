"""Configuration models for Plato worlds."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from plato._generated.models import (
    EnvFromArtifact,
    EnvFromResource,
    EnvFromSimulator,
)
from plato.v2.async_.session import SerializedSession

# Union type for environment configurations
EnvConfig = EnvFromArtifact | EnvFromSimulator | EnvFromResource


class AgentConfig(BaseModel):
    """Configuration for an agent.

    Attributes:
        image: Docker image URI for the agent
        config: Agent-specific configuration passed to the agent
    """

    image: str
    config: dict[str, Any] = Field(default_factory=dict)


class Agent:
    """Annotation marker for agent fields.

    Usage:
        coder: Annotated[AgentConfig, Agent(description="Coding agent")]
    """

    def __init__(self, description: str = "", required: bool = True):
        self.description = description
        self.required = required


class Secret:
    """Annotation marker for secret fields.

    Usage:
        api_key: Annotated[str | None, Secret(description="API key")] = None
    """

    def __init__(self, description: str = "", required: bool = False):
        self.description = description
        self.required = required


class Env:
    """Annotation marker for single environment fields.

    Environments are VMs that run alongside the world's runtime.
    They can be specified by artifact ID, simulator name, or resource config.

    Usage:
        gitea: Annotated[EnvConfig, Env(description="Git server")] = EnvFromArtifact(
            artifact_id="abc123",
            alias="gitea",
        )
    """

    def __init__(self, description: str = "", required: bool = True):
        self.description = description
        self.required = required


class EnvList:
    """Annotation marker for a list of arbitrary environments.

    Use this when the world accepts a dynamic list of environments
    rather than named, fixed environment fields.

    Usage:
        envs: Annotated[
            list[EnvFromSimulator | EnvFromArtifact | EnvFromResource],
            EnvList(description="Environments to create for this task"),
            Field(discriminator="type"),
        ] = []
    """

    def __init__(self, description: str = ""):
        self.description = description


class StateConfig(BaseModel):
    """Configuration for world state persistence.

    The state directory is a git-tracked directory that persists across checkpoints.
    At each checkpoint, the state directory is git bundled and uploaded as an artifact.
    On restore, bootstrap.sh downloads and unbundles the state before the world starts.

    Attributes:
        enabled: Whether to enable state persistence (default: True).
        path: Path to the state directory (default: /state).
    """

    enabled: bool = True
    path: str = "/state"


class CheckpointConfig(BaseModel):
    """Configuration for automatic checkpointing during world execution.

    Attributes:
        enabled: Whether to enable automatic checkpoints after steps (default: False).
        interval: Create checkpoint every N steps (default: 1 = every step).
        exclude_envs: Environment aliases to exclude from checkpoints (default: ["runtime"]).
    """

    enabled: bool = False
    interval: int = 1
    exclude_envs: list[str] = Field(default_factory=lambda: ["runtime"])


class RunConfig(BaseModel):
    """Base configuration for running a world.

    Subclass this with your world-specific fields, agents, secrets, and envs:

        class CodeWorldConfig(RunConfig):
            # World-specific fields
            repository_url: str
            prompt: str

            # Agents (typed)
            coder: Annotated[AgentConfig, Agent(description="Coding agent")]

            # Secrets (typed)
            git_token: Annotated[str | None, Secret(description="GitHub token")] = None

            # Environments (typed)
            gitea: Annotated[EnvConfig, Env(description="Git server")] = EnvFromArtifact(
                artifact_id="abc123",
                alias="gitea",
            )

    Attributes:
        session_id: Unique Chronos session identifier
        otel_url: OTel endpoint URL (e.g., https://chronos.plato.so/api/otel)
        upload_url: Presigned S3 URL for uploading artifacts (provided by Chronos)
        plato_session: Serialized Plato session for connecting to existing VM session
        checkpoint: Configuration for automatic checkpoints after steps
    """

    session_id: str = ""
    otel_url: str = ""  # OTel endpoint URL
    upload_url: str = ""  # Presigned S3 URL for uploads

    # Serialized Plato session for connecting to VM and sending heartbeats
    # This is the output of Session.dump() - used to restore session with Session.load()
    plato_session: SerializedSession | None = None

    # Checkpoint configuration for automatic snapshots after steps
    checkpoint: CheckpointConfig = Field(default_factory=CheckpointConfig)

    # State persistence configuration
    state: StateConfig = Field(default_factory=StateConfig)

    model_config = {"extra": "allow"}

    @classmethod
    def get_field_annotations(cls) -> dict[str, Agent | Secret | Env | EnvList | None]:
        """Get Agent/Secret/Env/EnvList annotations for each field."""
        result: dict[str, Agent | Secret | Env | EnvList | None] = {}

        for field_name, field_info in cls.model_fields.items():
            marker = None

            # Pydantic stores Annotated metadata in field_info.metadata
            for meta in field_info.metadata:
                if isinstance(meta, (Agent, Secret, Env, EnvList)):
                    marker = meta
                    break

            result[field_name] = marker

        return result

    @classmethod
    def get_json_schema(cls) -> dict:
        """Get JSON schema with agents, secrets, and envs separated."""
        # Get full Pydantic schema
        full_schema = cls.model_json_schema()
        full_schema.pop("title", None)

        # Separate fields by annotation type
        annotations = cls.get_field_annotations()
        properties = full_schema.get("properties", {})

        world_properties = {}
        agents = []
        secrets = []
        envs = []
        env_list_field: dict | None = None  # For EnvList marker (arbitrary envs)

        # Skip runtime fields
        runtime_fields = {"session_id", "otel_url", "upload_url", "plato_session", "checkpoint", "state"}

        for field_name, prop_schema in properties.items():
            if field_name in runtime_fields:
                continue

            marker = annotations.get(field_name)

            if isinstance(marker, Agent):
                agents.append(
                    {
                        "name": field_name,
                        "description": marker.description,
                        "required": marker.required,
                    }
                )
            elif isinstance(marker, Secret):
                secrets.append(
                    {
                        "name": field_name,
                        "description": marker.description,
                        "required": marker.required,
                    }
                )
            elif isinstance(marker, Env):
                # Get default value for this env field
                field_info = cls.model_fields.get(field_name)
                default_value = None
                if field_info and field_info.default is not None:
                    # Serialize the default EnvConfig to dict
                    default_env = field_info.default
                    if hasattr(default_env, "model_dump"):
                        default_value = default_env.model_dump()
                    elif isinstance(default_env, dict):
                        default_value = default_env

                envs.append(
                    {
                        "name": field_name,
                        "description": marker.description,
                        "required": marker.required,
                        "default": default_value,
                    }
                )
            elif isinstance(marker, EnvList):
                # Field marked as a list of arbitrary environments
                env_list_field = {
                    "name": field_name,
                    "description": marker.description,
                }
            else:
                world_properties[field_name] = prop_schema

        # Compute required fields (excluding runtime and annotated fields)
        required = [
            r for r in full_schema.get("required", []) if r not in runtime_fields and annotations.get(r) is None
        ]

        result = {
            "properties": world_properties,
            "required": required,
            "agents": agents,
            "secrets": secrets,
            "envs": envs,
        }

        # Include $defs if present (for nested type references)
        if "$defs" in full_schema:
            result["$defs"] = full_schema["$defs"]

        # Add env_list if present (for worlds with arbitrary environment lists)
        if env_list_field:
            result["env_list"] = env_list_field

        return result

    def get_envs(self) -> list[EnvConfig]:
        """Get all environment configurations from this config.

        Returns:
            List of EnvConfig objects (EnvFromArtifact, EnvFromSimulator, or EnvFromResource)
        """
        annotations = self.get_field_annotations()
        envs: list[EnvConfig] = []

        for field_name, marker in annotations.items():
            if isinstance(marker, Env):
                value = getattr(self, field_name, None)
                if value is not None:
                    envs.append(value)

        return envs

    @classmethod
    def from_file(cls, path: str | Path) -> RunConfig:
        """Load config from a JSON file."""
        import json

        path = Path(path)
        with open(path) as f:
            data = json.load(f)

        return cls._from_dict(data)

    @classmethod
    def _from_dict(cls, data: dict) -> RunConfig:
        """Parse config from a dictionary, handling nested structures."""
        annotations = cls.get_field_annotations()
        parsed: dict[str, Any] = {}

        # Handle world_config if present (for backwards compatibility)
        world_config = data.pop("world_config", {})

        # Handle agents dict -> individual agent fields
        agents_dict = data.pop("agents", {})

        # Handle secrets dict -> individual secret fields (for schema validation)
        secrets_dict = data.pop("secrets", {})  # Pop but don't store separately

        # Check if there's an EnvList field - if so, don't pop envs as a dict
        has_env_list = any(isinstance(m, EnvList) for m in annotations.values())

        # Handle envs dict -> individual env fields (only for named Env pattern)
        envs_dict: dict = {}
        if not has_env_list:
            envs_dict = data.pop("envs", {})

        # Merge world_config into top-level
        parsed.update(world_config)
        parsed.update(data)

        # Map agents dict to typed fields
        for field_name, marker in annotations.items():
            if isinstance(marker, Agent) and field_name in agents_dict:
                agent_data = agents_dict[field_name]
                if isinstance(agent_data, dict):
                    parsed[field_name] = AgentConfig(**agent_data)
                else:
                    parsed[field_name] = AgentConfig(image=str(agent_data))
            elif isinstance(marker, Secret) and field_name in secrets_dict:
                parsed[field_name] = secrets_dict[field_name]
            elif isinstance(marker, Env) and field_name in envs_dict:
                env_data = envs_dict[field_name]
                if isinstance(env_data, dict):
                    parsed[field_name] = _parse_env_config(env_data)
                else:
                    parsed[field_name] = env_data
            elif isinstance(marker, EnvList) and field_name in parsed:
                # Parse list of env configs
                env_list = parsed[field_name]
                if isinstance(env_list, list):
                    parsed[field_name] = [_parse_env_config(e) if isinstance(e, dict) else e for e in env_list]

        return cls(**parsed)


def _parse_env_config(data: dict) -> EnvConfig:
    """Parse an env config dict into the appropriate type."""
    if "artifact_id" in data:
        return EnvFromArtifact(**data)
    elif "sim_config" in data:
        return EnvFromResource(**data)
    else:
        return EnvFromSimulator(**data)
