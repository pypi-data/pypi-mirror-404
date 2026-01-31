"""List Registry Agents"""

from __future__ import annotations

from typing import Any

import httpx

from plato.chronos.errors import raise_for_status
from plato.chronos.models import AgentListResponse


def _build_request_args() -> dict[str, Any]:
    """Build request arguments."""
    url = "/api/registry/agents"

    return {
        "method": "GET",
        "url": url,
    }


def sync(
    client: httpx.Client,
) -> AgentListResponse:
    """List all agents from the registry with their ECR image URIs."""

    request_args = _build_request_args()

    response = client.request(**request_args)
    raise_for_status(response)
    return AgentListResponse.model_validate(response.json())


async def asyncio(
    client: httpx.AsyncClient,
) -> AgentListResponse:
    """List all agents from the registry with their ECR image URIs."""

    request_args = _build_request_args()

    response = await client.request(**request_args)
    raise_for_status(response)
    return AgentListResponse.model_validate(response.json())
