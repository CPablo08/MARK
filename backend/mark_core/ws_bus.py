"""In-process WebSocket fan-out (used when Redis pub/sub is unavailable)."""
import json
from datetime import datetime, timezone
from typing import Any

from fastapi import WebSocket

_connections: dict[str, set[WebSocket]] = {}


def register(user_id: str, ws: WebSocket) -> None:
    _connections.setdefault(user_id, set()).add(ws)


def unregister(user_id: str, ws: WebSocket) -> None:
    if user_id in _connections:
        _connections[user_id].discard(ws)
        if not _connections[user_id]:
            del _connections[user_id]


async def broadcast_local(user_id: str, event_type: str, payload: dict[str, Any]) -> None:
    envelope = json.dumps(
        {
            "type": event_type,
            "payload": payload,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    )
    dead: list[WebSocket] = []
    for ws in list(_connections.get(user_id, set())):
        try:
            await ws.send_text(envelope)
        except Exception:
            dead.append(ws)
    for ws in dead:
        unregister(user_id, ws)
