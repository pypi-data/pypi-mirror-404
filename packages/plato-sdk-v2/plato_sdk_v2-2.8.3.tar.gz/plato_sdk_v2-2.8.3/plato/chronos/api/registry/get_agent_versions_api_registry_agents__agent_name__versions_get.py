"""Get Agent Versions"""

from __future__ import annotations

from typing import Any

import httpx

from plato.chronos.errors import raise_for_status
from plato.chronos.models import AgentVersionsResponse


def _build_request_args(
    agent_name: str,
) -> dict[str, Any]:
    """Build request arguments."""
    url = f"/api/registry/agents/{agent_name}/versions"

    return {
        "method": "GET",
        "url": url,
    }


def sync(
    client: httpx.Client,
    agent_name: str,
) -> AgentVersionsResponse:
    """Get versions for an agent from the registry."""

    request_args = _build_request_args(
        agent_name=agent_name,
    )

    response = client.request(**request_args)
    raise_for_status(response)
    return AgentVersionsResponse.model_validate(response.json())


async def asyncio(
    client: httpx.AsyncClient,
    agent_name: str,
) -> AgentVersionsResponse:
    """Get versions for an agent from the registry."""

    request_args = _build_request_args(
        agent_name=agent_name,
    )

    response = await client.request(**request_args)
    raise_for_status(response)
    return AgentVersionsResponse.model_validate(response.json())
