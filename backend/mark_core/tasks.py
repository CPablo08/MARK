import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from mark_core.events import append_task_event, get_redis, publish_ws, push_execution_feed
from mark_core.models import Task, TaskEvent, TaskStatus, User


TASK_QUEUE = "mark:task_queue"


async def create_task(
    db: AsyncSession,
    user: User,
    title: str,
    objective: str,
    session_id: uuid.UUID | None = None,
    parent_task_id: uuid.UUID | None = None,
    enqueue: bool = True,
) -> Task:
    task = Task(
        user_id=user.id,
        title=title,
        objective=objective,
        status=TaskStatus.pending,
        progress=0.0,
        safety_mode_snapshot=user.safety_mode.value,
        session_id=session_id,
        parent_task_id=parent_task_id,
    )
    db.add(task)
    await db.flush()

    await append_task_event(str(task.id), "task.created", {"title": title})
    if enqueue:
        await enqueue_task(str(task.id), str(user.id))
    return task


async def enqueue_task(task_id: str, user_id: str) -> None:
    r = await get_redis()
    if r:
        await r.lpush(TASK_QUEUE, f"{task_id}:{user_id}")
    else:
        # Inline processing when Redis unavailable (local dev)
        import asyncio
        from mark_core.worker import process_task
        asyncio.create_task(process_task(task_id, user_id))


async def update_task_status(
    db: AsyncSession,
    task: Task,
    status: TaskStatus,
    progress: float | None = None,
    *,
    result: dict | None = None,
) -> Task:
    task.status = status
    if progress is not None:
        task.progress = progress
    task.updated_at = datetime.now(timezone.utc)
    await db.flush()

    payload = {
        "task_id": str(task.id),
        "title": task.title,
        "status": status.value,
        "progress": task.progress,
        "objective": task.objective,
    }
    if result:
        payload.update(result)
        await log_task_event(db, task.id, "task.result", result)
        from mark_core.task_reports import cache_task_report

        cache_task_report(
            str(task.user_id),
            {**payload, "objective": task.objective},
        )
    await publish_ws(str(task.user_id), "task.updated", payload)
    await append_task_event(str(task.id), "task.updated", payload)
    return task


async def log_task_event(db: AsyncSession, task_id: uuid.UUID, event_type: str, payload: dict) -> None:
    ev = TaskEvent(task_id=task_id, type=event_type, payload_json=payload)
    db.add(ev)
    await db.flush()


async def list_tasks(db: AsyncSession, user_id: uuid.UUID) -> list[Task]:
    result = await db.execute(
        select(Task).where(Task.user_id == user_id).order_by(Task.created_at.desc()).limit(100)
    )
    return list(result.scalars().all())


async def get_task(db: AsyncSession, task_id: uuid.UUID, user_id: uuid.UUID) -> Task | None:
    result = await db.execute(
        select(Task).where(Task.id == task_id, Task.user_id == user_id)
    )
    return result.scalar_one_or_none()


async def emit_agent_status(
    user_id: str,
    agent_id: str,
    role: str,
    status: str,
    task_id: str | None = None,
    message: str | None = None,
) -> None:
    await publish_ws(
        user_id,
        "agent.status",
        {
            "agent_id": agent_id,
            "role": role,
            "status": status,
            "task_id": task_id,
            "message": message,
        },
    )


async def feed(user_id: str, task_id: str, line: str, level: str = "info") -> None:
    await push_execution_feed(user_id, task_id, line, level)
    try:
        from mark_core.db import SessionLocal

        async with SessionLocal() as db:
            await log_task_event(
                db,
                uuid.UUID(task_id),
                "execution.feed",
                {"line": line, "level": level},
            )
            await db.commit()
    except Exception:
        pass
