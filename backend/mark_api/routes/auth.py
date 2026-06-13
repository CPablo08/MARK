from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from mark_core.auth import create_access_token, get_current_user, get_or_create_local_user
from mark_core.config import get_settings
from mark_core.db import get_db
from mark_core.models import SafetyMode, User

router = APIRouter()
settings = get_settings()


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str = ""
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: str
    email: str
    safety_mode: str
    settings: dict


class SettingsPatch(BaseModel):
    safety_mode: str | None = None


@router.get("/session", response_model=TokenResponse)
async def session(db: AsyncSession = Depends(get_db)):
    """Personal install: return a long-lived token for the local owner (no login)."""
    if not settings.personal_mode:
        raise HTTPException(status_code=404, detail="Not available")
    user = await get_or_create_local_user(db)
    return TokenResponse(access_token=create_access_token(str(user.id)))


@router.get("/me", response_model=UserResponse)
async def me(user: User = Depends(get_current_user)):
    return UserResponse(
        id=str(user.id),
        email=user.email,
        safety_mode=user.safety_mode.value,
        settings=user.settings_json or {},
    )


@router.patch("/settings", response_model=UserResponse)
async def patch_settings(
    body: SettingsPatch,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if body.safety_mode:
        user.safety_mode = SafetyMode(body.safety_mode)
    await db.flush()
    return UserResponse(
        id=str(user.id),
        email=user.email,
        safety_mode=user.safety_mode.value,
        settings=user.settings_json or {},
    )
