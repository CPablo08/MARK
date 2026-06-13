from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from mark_core.auth import get_current_user
from mark_core.db import get_db
from mark_core.models import AuditLog, User

router = APIRouter()


class LogResponse(BaseModel):
    id: str
    action: str
    actor: str
    payload: dict
    created_at: str


@router.get("", response_model=list[LogResponse])
async def get_logs(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(AuditLog)
        .where(AuditLog.user_id == user.id)
        .order_by(AuditLog.created_at.desc())
        .limit(200)
    )
    logs = result.scalars().all()
    return [
        LogResponse(
            id=str(l.id),
            action=l.action,
            actor=l.actor,
            payload=l.payload_json or {},
            created_at=l.created_at.isoformat(),
        )
        for l in logs
    ]
