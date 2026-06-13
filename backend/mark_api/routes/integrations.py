import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from mark_core.auth import get_current_user
from mark_core.db import get_db
from mark_core.models import Integration, User
from mark_tools.mcp_host import list_mcp_tools, reload_mcp_servers
from mark_tools.registry import TOOLS

router = APIRouter()


class IntegrationResponse(BaseModel):
    id: str
    name: str
    type: str
    enabled: bool
    config: dict


class IntegrationPatch(BaseModel):
    enabled: bool


class IntegrationCreate(BaseModel):
    name: str
    type: str = "mcp"
    enabled: bool = True
    config: dict = {}


class IntegrationUpdate(BaseModel):
    name: str | None = None
    enabled: bool | None = None
    config: dict | None = None


class ToolInfo(BaseModel):
    name: str
    description: str
    tags: list[str]
    source: str


class PluginsCatalog(BaseModel):
    integrations: list[IntegrationResponse]
    builtin_tools: list[ToolInfo]
    mcp_tools: list[ToolInfo]


async def _ensure_mark_plugins(db: AsyncSession, user: User, items: list[Integration]) -> list[Integration]:
    """Add built-in Visualize + Cam if missing (existing installs)."""
    names = {i.name for i in items}
    added = False
    if "Visualize" not in names:
        db.add(
            Integration(
                user_id=user.id,
                name="Visualize",
                type="mark",
                enabled=True,
                config_json={"plugin": "visualize", "builtin": True},
            )
        )
        added = True
    if "Cam" not in names:
        db.add(
            Integration(
                user_id=user.id,
                name="Cam",
                type="skill",
                enabled=True,
                config_json={"skill": "cam", "builtin": True},
            )
        )
        added = True
    if added:
        await db.flush()
        result = await db.execute(select(Integration).where(Integration.user_id == user.id))
        return list(result.scalars().all())
    return items


async def _seed_integrations(db: AsyncSession, user: User) -> list[Integration]:
    result = await db.execute(select(Integration).where(Integration.user_id == user.id))
    items = list(result.scalars().all())
    if items:
        return await _ensure_mark_plugins(db, user, items)
    from mark_core.config import get_settings

    root = str(get_settings().sandbox_dir)
    defaults = [
        Integration(
            user_id=user.id,
            name="Playwright MCP",
            type="mcp",
            enabled=True,
            config_json={
                "command": "npx",
                "args": ["-y", "@playwright/mcp@latest"],
            },
        ),
        Integration(
            user_id=user.id,
            name="Chrome DevTools MCP",
            type="mcp",
            enabled=False,
            config_json={
                "command": "npx",
                "args": ["-y", "chrome-devtools-mcp@latest", "--no-usage-statistics"],
            },
        ),
        Integration(
            user_id=user.id,
            name="Filesystem MCP",
            type="mcp",
            enabled=False,
            config_json={
                "command": "npx",
                "args": ["-y", "@modelcontextprotocol/server-filesystem", root],
            },
        ),
        Integration(
            user_id=user.id,
            name="GitHub MCP",
            type="mcp",
            enabled=False,
            config_json={"command": "npx", "args": ["-y", "@modelcontextprotocol/server-github"]},
        ),
        Integration(
            user_id=user.id,
            name="Visualize",
            type="mark",
            enabled=True,
            config_json={"plugin": "visualize", "builtin": True},
        ),
        Integration(
            user_id=user.id,
            name="Cam",
            type="skill",
            enabled=True,
            config_json={"skill": "cam", "builtin": True},
        ),
    ]
    for i in defaults:
        db.add(i)
    await db.flush()
    return defaults


async def _reload_mcp(items: list[Integration]) -> None:
    enabled = [
        {"name": i.name, **(i.config_json or {})}
        for i in items
        if i.enabled and i.type == "mcp"
    ]
    await reload_mcp_servers(enabled)


def _sync_mcp(items: list[Integration]) -> None:
    """Fire-and-forget when called without await (legacy)."""
    load_mcp_servers(
        [
            {"name": i.name, **(i.config_json or {})}
            for i in items
            if i.enabled and i.type == "mcp"
        ]
    )


@router.get("/catalog", response_model=PluginsCatalog)
async def plugins_catalog(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    items = await _seed_integrations(db, user)
    await db.commit()
    await _reload_mcp(items)

    builtin = [
        ToolInfo(
            name=t.name,
            description=t.description,
            tags=sorted(t.tags),
            source="builtin",
        )
        for t in TOOLS.values()
    ]
    mcp = [
        ToolInfo(
            name=t["name"],
            description=t["description"],
            tags=sorted(t.get("tags", [])),
            source="mcp",
        )
        for t in list_mcp_tools()
    ]

    return PluginsCatalog(
        integrations=[
            IntegrationResponse(
                id=str(i.id),
                name=i.name,
                type=i.type,
                enabled=i.enabled,
                config=i.config_json or {},
            )
            for i in items
        ],
        builtin_tools=builtin,
        mcp_tools=mcp,
    )


@router.get("", response_model=list[IntegrationResponse])
async def list_integrations(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    catalog = await plugins_catalog(user, db)
    return catalog.integrations


@router.post("", response_model=IntegrationResponse)
async def create_integration(
    body: IntegrationCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    item = Integration(
        user_id=user.id,
        name=body.name,
        type=body.type,
        enabled=body.enabled,
        config_json=body.config,
    )
    db.add(item)
    await db.flush()
    await db.commit()
    result = await db.execute(select(Integration).where(Integration.user_id == user.id))
    await _reload_mcp(list(result.scalars().all()))
    return IntegrationResponse(
        id=str(item.id),
        name=item.name,
        type=item.type,
        enabled=item.enabled,
        config=item.config_json or {},
    )


@router.put("/{integration_id}", response_model=IntegrationResponse)
async def update_integration(
    integration_id: str,
    body: IntegrationUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Integration).where(
            Integration.id == uuid.UUID(integration_id),
            Integration.user_id == user.id,
        )
    )
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Integration not found")
    if body.name is not None:
        item.name = body.name
    if body.enabled is not None:
        item.enabled = body.enabled
    if body.config is not None:
        item.config_json = body.config
    await db.flush()
    await db.commit()
    all_items = await _seed_integrations(db, user)
    await _reload_mcp(all_items)
    return IntegrationResponse(
        id=str(item.id),
        name=item.name,
        type=item.type,
        enabled=item.enabled,
        config=item.config_json or {},
    )


@router.delete("/{integration_id}")
async def delete_integration(
    integration_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Integration).where(
            Integration.id == uuid.UUID(integration_id),
            Integration.user_id == user.id,
        )
    )
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Integration not found")
    await db.delete(item)
    await db.flush()
    await db.commit()
    all_items = await _seed_integrations(db, user)
    await _reload_mcp(all_items)
    return {"ok": True}


@router.patch("/{integration_id}", response_model=IntegrationResponse)
async def patch_integration(
    integration_id: str,
    body: IntegrationPatch,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Integration).where(
            Integration.id == uuid.UUID(integration_id),
            Integration.user_id == user.id,
        )
    )
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Integration not found")
    item.enabled = body.enabled
    await db.flush()
    await db.commit()

    all_items = await _seed_integrations(db, user)
    await _reload_mcp(all_items)

    return IntegrationResponse(
        id=str(item.id),
        name=item.name,
        type=item.type,
        enabled=item.enabled,
        config=item.config_json or {},
    )
