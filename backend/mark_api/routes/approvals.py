from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from mark_core.auth import get_current_user
from mark_core.db import get_db
from mark_core.models import User
from mark_core.safety import resolve_approval

router = APIRouter()


class ResolveBody(BaseModel):
    approved: bool


@router.post("/{approval_id}/resolve")
async def resolve(
    approval_id: UUID,
    body: ResolveBody,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    approval = await resolve_approval(db, approval_id, user.id, body.approved)
    if not approval:
        raise HTTPException(status_code=404, detail="Approval not found")
    return {"ok": True, "status": approval.status}
