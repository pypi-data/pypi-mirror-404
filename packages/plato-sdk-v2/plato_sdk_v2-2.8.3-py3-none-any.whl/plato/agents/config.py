"""Typed configuration for Plato agents.

Provides base configuration classes that agents extend with their specific fields.
Secret fields are automatically loaded from environment variables using pydantic-settings.

Example:
    from plato.agents import AgentConfig, Secret
    from typing import Annotated

    class OpenHandsConfig(AgentConfig):
        model_name: str = "anthropic/claude-sonnet-4"
        anthropic_api_key: Annotated[str | None, Secret(description="API key")] = None

    # Secrets auto-loaded from env vars (ANTHROPIC_API_KEY -> anthropic_api_key)
    config = OpenHandsConfig.from_file("/config.json")
"""

from __future__ import annotations

import json
from typing import Any

from pydantic_settings import BaseSettings, SettingsConfigDict


class Secret:
    """Annotation marker for secret fields.

    Fields annotated with Secret are automatically loaded from environment variables.
    The env var name is the uppercase version of the field name (e.g., api_key -> API_KEY).

    Usage:
        api_key: Annotated[str, Secret(description="API key")]
    """

    def __init__(self, description: str = "", required: bool = False):
        self.description = description
        self.required = required


class AgentConfig(BaseSettings):
    """Base configuration for agents.

    Extends pydantic-settings BaseSettings, so secret fields are automatically loaded
    from environment variables. The env var name is the uppercase field name.

    Subclass with agent-specific fields:

        class OpenHandsConfig(AgentConfig):
            model_name: str = "anthropic/claude-sonnet-4"
            anthropic_api_key: Annotated[str | None, Secret(description="API key")] = None

        # ANTHROPIC_API_KEY env var is automatically loaded into anthropic_api_key
        config = OpenHandsConfig.from_file("/config.json")

    Attributes:
        logs_dir: Directory for agent logs and trajectory output.
    """

    model_config = SettingsConfigDict(
        env_prefix="",  # No prefix - ANTHROPIC_API_KEY maps to anthropic_api_key
        extra="allow",
        env_ignore_empty=True,
    )

    logs_dir: str = "/logs"

    @classmethod
    def get_field_secrets(cls) -> dict[str, Secret]:
        """Get Secret annotations for each field."""
        result: dict[str, Secret] = {}

        for field_name, field_info in cls.model_fields.items():
            for meta in field_info.metadata:
                if isinstance(meta, Secret):
                    result[field_name] = meta
                    break

        return result

    @classmethod
    def get_json_schema(cls) -> dict:
        """Get JSON schema with secrets separated."""
        full_schema = cls.model_json_schema()
        full_schema.pop("title", None)

        secrets_map = cls.get_field_secrets()
        properties = full_schema.get("properties", {})

        config_properties = {}
        secrets = []

        # Skip internal fields
        internal_fields = {"logs_dir"}

        for field_name, prop_schema in properties.items():
            if field_name in internal_fields:
                continue

            if field_name in secrets_map:
                secret = secrets_map[field_name]
                secrets.append(
                    {
                        "name": field_name,
                        "description": secret.description,
                        "required": secret.required,
                    }
                )
            else:
                config_properties[field_name] = prop_schema

        required = [r for r in full_schema.get("required", []) if r not in internal_fields and r not in secrets_map]

        return {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "type": "object",
            "properties": config_properties,
            "required": required,
            "secrets": secrets,
        }

    def get_secrets_dict(self) -> dict[str, str]:
        """Extract secret values as a dict for environment variables."""
        secrets_map = self.get_field_secrets()
        result: dict[str, str] = {}

        for field_name in secrets_map:
            value = getattr(self, field_name, None)
            if value is not None:
                result[field_name] = value

        return result

    def get_config_dict(self) -> dict[str, Any]:
        """Extract non-secret config values as a dict."""
        secrets_map = self.get_field_secrets()
        internal_fields = {"logs_dir"}

        result: dict[str, Any] = {}
        for field_name in self.model_fields:
            if field_name not in secrets_map and field_name not in internal_fields:
                value = getattr(self, field_name, None)
                if value is not None:
                    result[field_name] = value

        return result

    @classmethod
    def from_env(cls) -> AgentConfig:
        """Load config from AGENT_CONFIG_B64 environment variable.

        The runner passes config as base64-encoded JSON in the
        AGENT_CONFIG_B64 environment variable.
        """
        import base64
        import os

        config_b64 = os.environ.get("AGENT_CONFIG_B64")
        if not config_b64:
            raise ValueError("AGENT_CONFIG_B64 environment variable not set")
        config_json = base64.b64decode(config_b64).decode()
        data = json.loads(config_json)
        return cls(**data)
