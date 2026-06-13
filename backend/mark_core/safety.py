from __future__ import annotations

import asyncio
import time
import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from mark_core.db import SessionLocal
from mark_core.events import publish_ws
from mark_core.models import Approval, SafetyMode, User


DANGEROUS_TAGS = {"dangerous", "deploy", "shell", "write"}


def tool_requires_approval(user: User, tool_tags: set[str]) -> bool:
    mode = user.safety_mode
    if mode == SafetyMode.autonomous:
        return "dangerous" in tool_tags and "rm -rf" in str(tool_tags)
    if mode == SafetyMode.safe:
        return bool(tool_tags & DANGEROUS_TAGS) or "write" in tool_tags
    return bool(tool_tags & {"dangerous", "deploy"})


async def request_approval(
    db: AsyncSession,
    user: User,
    task_id: uuid.UUID,
    action: str,
    description: str,
    payload: dict[str, Any],
) -> Approval:
    approval = Approval(
        user_id=user.id,
        task_id=task_id,
        action=action,
        description=description,
        payload_json={**payload, "rollback_snapshot": payload.get("rollback_snapshot")},
        status="pending",
    )
    db.add(approval)
    await db.flush()

    ws_payload: dict[str, Any] = {
        "approval_id": str(approval.id),
        "action": action,
        "description": description,
        "payload": approval.payload_json,
    }
    ws_payload["task_id"] = str(task_id)

    await publish_ws(
        str(user.id),
        "approval.request",
        ws_payload,
    )
    return approval


async def request_chat_approval(
    db: AsyncSession,
    user: User,
    action: str,
    description: str,
    payload: dict[str, Any],
) -> Approval:
    """Approval from quick chat (no running task row). User must Approve/Deny in UI."""
    approval = Approval(
        user_id=user.id,
        task_id=None,
        action=action,
        description=description,
        payload_json=dict(payload),
        status="pending",
    )
    db.add(approval)
    await db.flush()

    await publish_ws(
        str(user.id),
        "approval.request",
        {
            "approval_id": str(approval.id),
            "task_id": "",
            "action": action,
            "description": description,
            "payload": approval.payload_json,
        },
    )
    return approval


async def wait_until_approval_resolved(
    approval_id: uuid.UUID, *, timeout_sec: float = 600.0, poll_sec: float = 0.35
) -> str:
    """Poll until approved / denied / timeout. Returns 'approved', 'denied', or 'timeout'."""
    deadline = time.monotonic() + timeout_sec
    while time.monotonic() < deadline:
        async with SessionLocal() as db:
            result = await db.execute(select(Approval).where(Approval.id == approval_id))
            row = result.scalar_one_or_none()
            if not row:
                return "denied"
            if row.status == "approved":
                return "approved"
            if row.status == "denied":
                return "denied"
        await asyncio.sleep(poll_sec)
    return "timeout"


async def resolve_approval(
    db: AsyncSession,
    approval_id: uuid.UUID,
    user_id: uuid.UUID,
    approved: bool,
) -> Approval | None:
    result = await db.execute(
        select(Approval).where(Approval.id == approval_id, Approval.user_id == user_id)
    )
    approval = result.scalar_one_or_none()
    if not approval:
        return None
    approval.status = "approved" if approved else "denied"
    approval.resolved_by = user_id
    await db.flush()

    tid = str(approval.task_id) if approval.task_id else ""
    await publish_ws(
        str(user_id),
        "approval.resolve",
        {"approval_id": str(approval.id), "task_id": tid, "approved": approved},
    )
    return approval
