import json
from datetime import datetime, timezone
from typing import Any

import redis.asyncio as redis

from mark_core.config import get_settings
from mark_core.ws_bus import broadcast_local

settings = get_settings()
_redis: redis.Redis | None = None
_redis_checked = False


async def get_redis() -> redis.Redis | None:
    global _redis, _redis_checked
    if _redis_checked:
        return _redis
    _redis_checked = True
    try:
        client = redis.from_url(settings.redis_url, decode_responses=True)
        await client.ping()
        _redis = client
    except Exception:
        _redis = None
    return _redis


def ws_channel(user_id: str) -> str:
    return f"mark:ws:{user_id}"


def task_stream_key(task_id: str) -> str:
    return f"mark:events:{task_id}"


async def publish_ws(user_id: str, event_type: str, payload: dict[str, Any]) -> None:
    """Deliver to connected clients via Redis and/or in-process bus."""
    envelope = {
        "type": event_type,
        "payload": payload,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    r = await get_redis()
    if r:
        await r.publish(ws_channel(user_id), json.dumps(envelope))
    else:
        await broadcast_local(user_id, event_type, payload)


async def append_task_event(task_id: str, event_type: str, payload: dict[str, Any]) -> None:
    r = await get_redis()
    if not r:
        return
    await r.xadd(
        task_stream_key(task_id),
        {"type": event_type, "payload": json.dumps(payload)},
        maxlen=5000,
    )
    await r.xadd(
        "mark:events:global",
        {"task_id": task_id, "type": event_type, "payload": json.dumps(payload)},
        maxlen=10000,
    )


async def push_execution_feed(user_id: str, task_id: str, line: str, level: str = "info") -> None:
    payload = {"task_id": task_id, "line": line, "level": level}
    await publish_ws(user_id, "execution.feed", payload)
    await append_task_event(task_id, "execution.feed", payload)
