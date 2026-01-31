"""Build configuration for Plato agents.

Reads [tool.plato.build] from pyproject.toml to configure Docker builds.

Example pyproject.toml:
    [tool.plato.build]
    env = { "SOME_BUILD_ARG" = "value" }
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

try:
    import tomllib
except ImportError:
    import tomli as tomllib


class BuildConfig(BaseModel):
    """Docker build configuration for an agent.

    Read from [tool.plato.build] in pyproject.toml.
    """

    env: dict[str, str] = Field(
        default_factory=dict,
        description="Environment variables to pass as build args",
    )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dict for schema output."""
        return self.model_dump(exclude_defaults=False)

    @classmethod
    def get_json_schema(cls) -> dict[str, Any]:
        """Get JSON schema for build config."""
        schema = cls.model_json_schema()
        schema.pop("title", None)
        return schema

    @classmethod
    def from_pyproject(cls, path: str | Path) -> BuildConfig:
        """Load build config from pyproject.toml."""
        path = Path(path)
        if path.is_dir():
            path = path / "pyproject.toml"

        with open(path, "rb") as f:
            data = tomllib.load(f)

        build_config = data.get("tool", {}).get("plato", {}).get("build", {})
        return cls(**build_config)


def load_build_config(agent_path: str | Path) -> BuildConfig:
    """Load build config from an agent directory."""
    return BuildConfig.from_pyproject(agent_path)
