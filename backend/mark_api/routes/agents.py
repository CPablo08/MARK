from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from mark_core.auth import get_current_user
from mark_core.db import get_db
from mark_core.models import Agent, User

router = APIRouter()


class AgentResponse(BaseModel):
    id: str
    role: str
    status: str
    task_id: str | None
    created_at: str


@router.get("", response_model=list[AgentResponse])
async def list_agents(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Agent).where(Agent.user_id == user.id).order_by(Agent.created_at.desc()).limit(50)
    )
    agents = result.scalars().all()
    return [
        AgentResponse(
            id=str(a.id),
            role=a.role,
            status=a.status,
            task_id=str(a.task_id) if a.task_id else None,
            created_at=a.created_at.isoformat(),
        )
        for a in agents
    ]
