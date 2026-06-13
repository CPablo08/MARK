import asyncio
import json
import logging
import uuid

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from mark_core.auth import decode_access_token, get_or_create_local_user
from mark_core.config import get_settings
from mark_core.db import SessionLocal
from mark_core.events import get_redis, publish_ws, ws_channel
from mark_core.ws_bus import broadcast_local, register, unregister

logger = logging.getLogger("mark.ws")
settings = get_settings()
ws_router = APIRouter()


async def resolve_ws_user_id(token: str) -> str | None:
    if settings.personal_mode:
        async with SessionLocal() as db:
            user = await get_or_create_local_user(db)
            await db.commit()
            return str(user.id)
    return decode_access_token(token)


@ws_router.websocket("/ws/v1")
async def websocket_endpoint(websocket: WebSocket, token: str = ""):
    user_id = await resolve_ws_user_id(token)
    if not user_id:
        await websocket.close(code=4001)
        return

    await websocket.accept()
    register(user_id, websocket)

    r = await get_redis()
    listener_task = None
    pubsub = None
    if r:
        pubsub = r.pubsub()
        await pubsub.subscribe(ws_channel(user_id), "mark:metrics")

        async def redis_listener():
            async for message in pubsub.listen():
                if message["type"] != "message":
                    continue
                data = message["data"]
                if isinstance(data, bytes):
                    data = data.decode()
                try:
                    parsed = json.loads(data)
                    await broadcast_local(
                        user_id, parsed.get("type", ""), parsed.get("payload", {})
                    )
                except json.JSONDecodeError:
                    await websocket.send_text(data)

        listener_task = asyncio.create_task(redis_listener())

    await broadcast_local(
        user_id,
        "metrics.snapshot",
        {
            "active_agents": 0,
            "queue_depth": 0,
            "tokens_used": 0,
            "system_health": "healthy",
        },
    )

    try:
        while True:
            raw = await websocket.receive_text()
            try:
                event = json.loads(raw)
            except json.JSONDecodeError:
                continue

            etype = event.get("type")
            if etype == "ping":
                await websocket.send_text(json.dumps({"type": "pong", "payload": {}}))
            elif etype == "approval.resolve":
                payload = event.get("payload", {})
                from mark_core.safety import resolve_approval

                async with SessionLocal() as db:
                    await resolve_approval(
                        db,
                        uuid.UUID(payload["approval_id"]),
                        uuid.UUID(user_id),
                        payload.get("approved", False),
                    )
                    await db.commit()
            elif etype == "voice.cancel":
                await publish_ws(user_id, "voice.audio", {"chunk": "", "format": "mp3", "done": True})
    except WebSocketDisconnect:
        pass
    finally:
        if listener_task:
            listener_task.cancel()
        if pubsub:
            await pubsub.unsubscribe(ws_channel(user_id))
        unregister(user_id, websocket)
