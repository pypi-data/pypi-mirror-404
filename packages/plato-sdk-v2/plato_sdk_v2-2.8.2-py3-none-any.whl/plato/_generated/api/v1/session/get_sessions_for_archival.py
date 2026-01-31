"""Get Sessions For Archival"""

from __future__ import annotations

from typing import Any

import httpx

from plato._generated.errors import raise_for_status
from plato._generated.models import SessionArchivalListResponse


def _build_request_args(
    page: int | None = 1,
    page_size: int | None = 10000,
    only_unarchived: bool | None = False,
    authorization: str | None = None,
    x_api_key: str | None = None,
) -> dict[str, Any]:
    """Build request arguments."""
    url = "/api/v1/session/archival/list"

    params: dict[str, Any] = {}
    if page is not None:
        params["page"] = page
    if page_size is not None:
        params["page_size"] = page_size
    if only_unarchived is not None:
        params["only_unarchived"] = only_unarchived

    headers: dict[str, str] = {}
    if authorization is not None:
        headers["authorization"] = authorization
    if x_api_key is not None:
        headers["X-API-Key"] = x_api_key

    return {
        "method": "GET",
        "url": url,
        "params": params,
        "headers": headers,
    }


def sync(
    client: httpx.Client,
    page: int | None = 1,
    page_size: int | None = 10000,
    only_unarchived: bool | None = False,
    authorization: str | None = None,
    x_api_key: str | None = None,
) -> SessionArchivalListResponse:
    """Lightweight endpoint to list sessions with archival-relevant fields only.
    Requires admin access.

    Returns minimal data (no joins) for fast bulk queries:
    - session_id, created_at, logs_archived_at, organization_id, simulator_id

    Use only_unarchived=true to filter to sessions that haven't been archived yet."""

    request_args = _build_request_args(
        page=page,
        page_size=page_size,
        only_unarchived=only_unarchived,
        authorization=authorization,
        x_api_key=x_api_key,
    )

    response = client.request(**request_args)
    raise_for_status(response)
    return SessionArchivalListResponse.model_validate(response.json())


async def asyncio(
    client: httpx.AsyncClient,
    page: int | None = 1,
    page_size: int | None = 10000,
    only_unarchived: bool | None = False,
    authorization: str | None = None,
    x_api_key: str | None = None,
) -> SessionArchivalListResponse:
    """Lightweight endpoint to list sessions with archival-relevant fields only.
    Requires admin access.

    Returns minimal data (no joins) for fast bulk queries:
    - session_id, created_at, logs_archived_at, organization_id, simulator_id

    Use only_unarchived=true to filter to sessions that haven't been archived yet."""

    request_args = _build_request_args(
        page=page,
        page_size=page_size,
        only_unarchived=only_unarchived,
        authorization=authorization,
        x_api_key=x_api_key,
    )

    response = await client.request(**request_args)
    raise_for_status(response)
    return SessionArchivalListResponse.model_validate(response.json())
