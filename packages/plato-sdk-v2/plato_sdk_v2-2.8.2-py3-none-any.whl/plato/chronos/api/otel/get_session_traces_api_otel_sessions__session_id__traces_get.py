"""Get Session Traces"""

from __future__ import annotations

from typing import Any

import httpx

from plato.chronos.errors import raise_for_status
from plato.chronos.models import OTelTraceResponse


def _build_request_args(
    session_id: str,
) -> dict[str, Any]:
    """Build request arguments."""
    url = f"/api/otel/sessions/{session_id}/traces"

    return {
        "method": "GET",
        "url": url,
    }


def sync(
    client: httpx.Client,
    session_id: str,
) -> OTelTraceResponse:
    """Get all parsed traces for a session.

    Returns spans parsed from stored OTLP batches, suitable for UI rendering."""

    request_args = _build_request_args(
        session_id=session_id,
    )

    response = client.request(**request_args)
    raise_for_status(response)
    return OTelTraceResponse.model_validate(response.json())


async def asyncio(
    client: httpx.AsyncClient,
    session_id: str,
) -> OTelTraceResponse:
    """Get all parsed traces for a session.

    Returns spans parsed from stored OTLP batches, suitable for UI rendering."""

    request_args = _build_request_args(
        session_id=session_id,
    )

    response = await client.request(**request_args)
    raise_for_status(response)
    return OTelTraceResponse.model_validate(response.json())
