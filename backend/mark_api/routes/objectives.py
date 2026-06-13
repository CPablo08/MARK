from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from mark_core.auth import get_current_user
from mark_core.db import get_db
from mark_core.models import Objective, User

router = APIRouter()


class ObjectiveResponse(BaseModel):
    id: str
    title: str
    progress: float
    status: str
    target_metric: str | None
    current_value: str | None


@router.get("", response_model=list[ObjectiveResponse])
async def get_objectives(
    user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Objective).where(Objective.user_id == user.id))
    objs = result.scalars().all()
    return [
        ObjectiveResponse(
            id=str(o.id),
            title=o.title,
            progress=o.progress,
            status=o.status,
            target_metric=o.target_metric,
            current_value=o.current_value,
        )
        for o in objs
    ]
