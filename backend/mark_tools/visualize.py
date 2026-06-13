"""Visualize plugin — push interactive HTML to the center workspace panel."""

from __future__ import annotations

import uuid
from typing import Any

from mark_core.events import publish_ws

_last_open: dict[str, dict[str, Any]] = {}


def pop_last_visualization(user_id: str) -> dict[str, Any] | None:
    """Consume visualization opened by the visualize tool this turn (not stale panels)."""
    return _last_open.pop(user_id, None)


def clear_pending_visualization(user_id: str) -> None:
    _last_open.pop(user_id, None)


async def open_visualization(
    user_id: str,
    *,
    title: str,
    html: str,
    description: str = "",
) -> dict[str, Any]:
    """Publish workspace panel payload; returns metadata for tool ack."""
    viz_id = str(uuid.uuid4())
    payload = {
        "id": viz_id,
        "title": title.strip() or "Visualization",
        "html": html,
        "description": description.strip(),
    }
    _last_open[user_id] = payload
    await publish_ws(user_id, "visualize.open", payload)
    return payload


async def close_visualization(user_id: str) -> None:
    await publish_ws(user_id, "visualize.close", {})
