"""Get Runtime"""

from __future__ import annotations

from typing import Any

import httpx

from plato.chronos.errors import raise_for_status
from plato.chronos.models import RuntimeResponse


def _build_request_args(
    artifact_id: str,
    x_api_key: str | None = None,
) -> dict[str, Any]:
    """Build request arguments."""
    url = f"/api/runtimes/{artifact_id}"

    headers: dict[str, str] = {}
    if x_api_key is not None:
        headers["X-API-Key"] = x_api_key

    return {
        "method": "GET",
        "url": url,
        "headers": headers,
    }


def sync(
    client: httpx.Client,
    artifact_id: str,
    x_api_key: str | None = None,
) -> RuntimeResponse:
    """Get a runtime by artifact ID."""

    request_args = _build_request_args(
        artifact_id=artifact_id,
        x_api_key=x_api_key,
    )

    response = client.request(**request_args)
    raise_for_status(response)
    return RuntimeResponse.model_validate(response.json())


async def asyncio(
    client: httpx.AsyncClient,
    artifact_id: str,
    x_api_key: str | None = None,
) -> RuntimeResponse:
    """Get a runtime by artifact ID."""

    request_args = _build_request_args(
        artifact_id=artifact_id,
        x_api_key=x_api_key,
    )

    response = await client.request(**request_args)
    raise_for_status(response)
    return RuntimeResponse.model_validate(response.json())
