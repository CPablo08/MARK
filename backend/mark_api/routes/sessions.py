import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from mark_core.auth import get_current_user
from mark_core.db import get_db
from mark_core.models import Message, Session, User

router = APIRouter()


class SessionSummary(BaseModel):
    id: str
    title: str
    created_at: str
    updated_at: str
    message_count: int


class ChatMessageResponse(BaseModel):
    id: str
    role: str
    content: str
    created_at: str


@router.get("", response_model=list[SessionSummary])
async def list_sessions(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Session)
        .where(Session.user_id == user.id)
        .order_by(Session.created_at.desc())
        .limit(100)
    )
    sessions = list(result.scalars().all())
    summaries: list[SessionSummary] = []
    for s in sessions:
        count_result = await db.execute(
            select(func.count()).select_from(Message).where(Message.session_id == s.id)
        )
        count = count_result.scalar() or 0
        last_msg = await db.execute(
            select(Message.created_at)
            .where(Message.session_id == s.id)
            .order_by(Message.created_at.desc())
            .limit(1)
        )
        updated = last_msg.scalar_one_or_none() or s.created_at
        summaries.append(
            SessionSummary(
                id=str(s.id),
                title=s.title,
                created_at=s.created_at.isoformat(),
                updated_at=updated.isoformat() if hasattr(updated, "isoformat") else s.created_at.isoformat(),
                message_count=count,
            )
        )
    return summaries


@router.get("/{session_id}/messages", response_model=list[ChatMessageResponse])
async def get_session_messages(
    session_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Session).where(
            Session.id == uuid.UUID(session_id),
            Session.user_id == user.id,
        )
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Session not found")

    msgs = await db.execute(
        select(Message)
        .where(Message.session_id == uuid.UUID(session_id))
        .order_by(Message.created_at.asc())
    )
    return [
        ChatMessageResponse(
            id=str(m.id),
            role=m.role,
            content=m.content,
            created_at=m.created_at.isoformat(),
        )
        for m in msgs.scalars().all()
    ]
