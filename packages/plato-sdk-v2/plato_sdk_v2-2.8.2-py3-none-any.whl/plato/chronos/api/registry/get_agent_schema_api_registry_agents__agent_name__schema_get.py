"""Get Agent Schema"""

from __future__ import annotations

from typing import Any

import httpx

from plato.chronos.errors import raise_for_status
from plato.chronos.models import ChronosApiRegistryAgentSchemaResponse


def _build_request_args(
    agent_name: str,
    version: str | None = None,
) -> dict[str, Any]:
    """Build request arguments."""
    url = f"/api/registry/agents/{agent_name}/schema"

    params: dict[str, Any] = {}
    if version is not None:
        params["version"] = version

    return {
        "method": "GET",
        "url": url,
        "params": params,
    }


def sync(
    client: httpx.Client,
    agent_name: str,
    version: str | None = None,
) -> ChronosApiRegistryAgentSchemaResponse:
    """Get schema for an agent version from the registry."""

    request_args = _build_request_args(
        agent_name=agent_name,
        version=version,
    )

    response = client.request(**request_args)
    raise_for_status(response)
    return ChronosApiRegistryAgentSchemaResponse.model_validate(response.json())


async def asyncio(
    client: httpx.AsyncClient,
    agent_name: str,
    version: str | None = None,
) -> ChronosApiRegistryAgentSchemaResponse:
    """Get schema for an agent version from the registry."""

    request_args = _build_request_args(
        agent_name=agent_name,
        version=version,
    )

    response = await client.request(**request_args)
    raise_for_status(response)
    return ChronosApiRegistryAgentSchemaResponse.model_validate(response.json())
