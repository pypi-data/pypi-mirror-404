"""Get World Versions"""

from __future__ import annotations

from typing import Any

import httpx

from plato.chronos.errors import raise_for_status
from plato.chronos.models import WorldVersionsResponse


def _build_request_args(
    package_name: str,
) -> dict[str, Any]:
    """Build request arguments."""
    url = f"/api/registry/worlds/{package_name}/versions"

    return {
        "method": "GET",
        "url": url,
    }


def sync(
    client: httpx.Client,
    package_name: str,
) -> WorldVersionsResponse:
    """Get versions for a world package from the registry."""

    request_args = _build_request_args(
        package_name=package_name,
    )

    response = client.request(**request_args)
    raise_for_status(response)
    return WorldVersionsResponse.model_validate(response.json())


async def asyncio(
    client: httpx.AsyncClient,
    package_name: str,
) -> WorldVersionsResponse:
    """Get versions for a world package from the registry."""

    request_args = _build_request_args(
        package_name=package_name,
    )

    response = await client.request(**request_args)
    raise_for_status(response)
    return WorldVersionsResponse.model_validate(response.json())
