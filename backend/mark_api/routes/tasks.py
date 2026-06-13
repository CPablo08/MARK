import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from mark_core.auth import get_current_user
from mark_core.db import get_db
from mark_core.models import Task, TaskEvent, User
from mark_core.tasks import create_task, feed, get_task, list_tasks
from mark_core.worker import process_task

router = APIRouter()


class TaskCreate(BaseModel):
    title: str
    objective: str


class TaskResponse(BaseModel):
    id: str
    title: str
    objective: str
    status: str
    progress: float
    parent_task_id: str | None = None
    created_at: str
    updated_at: str


def _task(t) -> TaskResponse:
    return TaskResponse(
        id=str(t.id),
        title=t.title,
        objective=t.objective,
        status=t.status.value,
        progress=t.progress,
        parent_task_id=str(t.parent_task_id) if t.parent_task_id else None,
        created_at=t.created_at.isoformat(),
        updated_at=t.updated_at.isoformat(),
    )


@router.get("", response_model=list[TaskResponse])
async def get_tasks(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    tasks = await list_tasks(db, user.id)
    return [_task(t) for t in tasks]


class FeedLine(BaseModel):
    line: str
    level: str = "info"
    created_at: str


class TaskResultResponse(BaseModel):
    task_id: str
    title: str
    status: str
    result_message_id: str | None = None
    result_kind: str | None = None
    result_preview: str | None = None
    result_content: str | None = None


@router.get("/{task_id}/result", response_model=TaskResultResponse)
async def get_task_result(
    task_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        tid = uuid.UUID(task_id)
    except ValueError:
        raise HTTPException(404, "Task not found") from None
    task = await get_task(db, tid, user.id)
    if not task:
        raise HTTPException(404, "Task not found")

    result = await db.execute(
        select(TaskEvent)
        .where(TaskEvent.task_id == tid, TaskEvent.type == "task.result")
        .order_by(TaskEvent.created_at.desc())
        .limit(1)
    )
    ev = result.scalar_one_or_none()
    payload = (ev.payload_json or {}) if ev else {}

    return TaskResultResponse(
        task_id=str(task.id),
        title=task.title,
        status=task.status.value,
        result_message_id=payload.get("result_message_id"),
        result_kind=payload.get("result_kind"),
        result_preview=payload.get("result_preview"),
        result_content=payload.get("result_content"),
    )


@router.get("/{task_id}/feed", response_model=list[FeedLine])
async def get_task_feed(
    task_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        tid = uuid.UUID(task_id)
    except ValueError:
        raise HTTPException(404, "Task not found") from None
    task = await get_task(db, tid, user.id)
    if not task:
        raise HTTPException(404, "Task not found")
    result = await db.execute(
        select(TaskEvent)
        .where(TaskEvent.task_id == tid, TaskEvent.type == "execution.feed")
        .order_by(TaskEvent.created_at.asc())
        .limit(300)
    )
    lines: list[FeedLine] = []
    for ev in result.scalars().all():
        payload = ev.payload_json or {}
        lines.append(
            FeedLine(
                line=str(payload.get("line", "")),
                level=str(payload.get("level", "info")),
                created_at=ev.created_at.isoformat(),
            )
        )
    return lines


@router.post("", response_model=TaskResponse)
async def post_task(
    body: TaskCreate,
    background_tasks: BackgroundTasks,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    task = await create_task(db, user, body.title, body.objective, enqueue=False)
    await feed(str(user.id), str(task.id), "Task queued for autonomous execution.")
    await db.commit()
    background_tasks.add_task(process_task, str(task.id), str(user.id))
    return _task(task)
