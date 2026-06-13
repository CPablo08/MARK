"""Recent Operations task reports — for chat Q&A backed by results."""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from mark_core.models import Task, TaskEvent

# user_id -> newest first
_cache: dict[str, list[dict[str, Any]]] = {}
_MAX = 10


def cache_task_report(user_id: str, data: dict[str, Any]) -> None:
    entry = {
        "task_id": data.get("task_id", ""),
        "title": data.get("title", "Task"),
        "status": data.get("status", "completed"),
        "objective": data.get("objective", ""),
        "result_kind": data.get("result_kind"),
        "result_preview": data.get("result_preview", ""),
        "result_content": data.get("result_content", ""),
    }
    if not entry["result_content"] and not entry["result_preview"]:
        return
    items = _cache.setdefault(user_id, [])
    items = [e for e in items if e.get("task_id") != entry["task_id"]]
    items.insert(0, entry)
    _cache[user_id] = items[:_MAX]


def list_cached_reports(user_id: str, limit: int = 5) -> list[dict[str, Any]]:
    return list(_cache.get(user_id, [])[:limit])


async def load_report_from_db(
    db: AsyncSession,
    user_id: uuid.UUID,
    task_id: uuid.UUID,
) -> dict[str, Any] | None:
    task = await db.get(Task, task_id)
    if not task or task.user_id != user_id:
        return None
    result = await db.execute(
        select(TaskEvent)
        .where(TaskEvent.task_id == task_id, TaskEvent.type == "task.result")
        .order_by(TaskEvent.created_at.desc())
        .limit(1)
    )
    ev = result.scalar_one_or_none()
    payload = dict(ev.payload_json or {}) if ev else {}
    return {
        "task_id": str(task.id),
        "title": task.title,
        "status": task.status.value,
        "objective": task.objective,
        "result_kind": payload.get("result_kind"),
        "result_preview": payload.get("result_preview", ""),
        "result_content": payload.get("result_content", ""),
    }


async def resolve_report(
    db: AsyncSession | None,
    user_id: str,
    task_id: str | None = None,
) -> dict[str, Any] | None:
    if task_id:
        try:
            tid = uuid.UUID(task_id)
        except ValueError:
            return None
        if db:
            row = await load_report_from_db(db, uuid.UUID(user_id), tid)
            if row:
                return row
        for r in _cache.get(user_id, []):
            if r.get("task_id") == task_id:
                return r
        return None
    cached = _cache.get(user_id, [])
    if cached:
        return cached[0]
    if db:
        result = await db.execute(
            select(Task)
            .where(Task.user_id == uuid.UUID(user_id))
            .order_by(Task.updated_at.desc())
            .limit(1)
        )
        task = result.scalar_one_or_none()
        if task and task.status.value in ("completed", "failed"):
            return await load_report_from_db(db, uuid.UUID(user_id), task.id)
    return None


def format_report_for_prompt(report: dict[str, Any], *, max_chars: int = 12_000) -> str:
    body = (report.get("result_content") or report.get("result_preview") or "").strip()
    if len(body) > max_chars:
        body = body[:max_chars] + "\n\n…(truncated for context)"
    return (
        f"Task ID: {report.get('task_id')}\n"
        f"Title: {report.get('title')}\n"
        f"Status: {report.get('status')}\n"
        f"Objective: {report.get('objective')}\n"
        f"Kind: {report.get('result_kind') or 'report'}\n\n"
        f"--- Report body ---\n{body}"
    )
