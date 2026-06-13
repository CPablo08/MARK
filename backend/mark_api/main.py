import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from mark_api.routes import agents, approvals, auth, chat, health, integrations, logs, media, memory, objectives, sessions, skills, tasks, voice
from mark_api.websocket import ws_router
from mark_core.auth import ensure_local_user
from mark_core.config import get_settings
from mark_core.db import SessionLocal, engine
from mark_core.models import Base
from mark_memory.qdrant_client import ensure_collection
from mark_tools.mcp_host import reload_mcp_servers, shutdown_mcp_servers
import mark_tools.builtin  # noqa: F401 — register built-in tools

logger = logging.getLogger("mark.api")
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    try:
        ensure_collection()
    except Exception as e:
        logger.warning("Qdrant not available at startup: %s", e)
    if get_settings().personal_mode:
        async with SessionLocal() as db:
            await ensure_local_user(db)
            await db.commit()
        logger.info("Personal mode: local owner ready")
        try:
            from sqlalchemy import select
            from mark_core.models import Integration

            async with SessionLocal() as db:
                user = await ensure_local_user(db)
                result = await db.execute(
                    select(Integration).where(Integration.user_id == user.id, Integration.enabled.is_(True))
                )
                configs = [
                    {"name": i.name, **(i.config_json or {})}
                    for i in result.scalars().all()
                    if i.type == "mcp"
                ]
                await db.commit()
            if configs:
                await reload_mcp_servers(configs)
        except Exception as e:
            logger.warning("MCP startup load skipped: %s", e)
    yield
    await shutdown_mcp_servers()
    from mark_tools.browser import shutdown_browser

    await shutdown_browser()
    await engine.dispose()


app = FastAPI(title="MARK API", version="0.1.0", lifespan=lifespan)

origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins + ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(tasks.router, prefix="/tasks", tags=["tasks"])
app.include_router(agents.router, prefix="/agents", tags=["agents"])
app.include_router(memory.router, prefix="/memory", tags=["memory"])
app.include_router(objectives.router, prefix="/objectives", tags=["objectives"])
app.include_router(integrations.router, prefix="/integrations", tags=["integrations"])
app.include_router(logs.router, prefix="/logs", tags=["logs"])
app.include_router(approvals.router, prefix="/approvals", tags=["approvals"])
app.include_router(sessions.router, prefix="/sessions", tags=["sessions"])
app.include_router(chat.router, tags=["chat"])
app.include_router(media.router)
app.include_router(skills.router, prefix="/skills", tags=["skills"])
app.include_router(voice.router)
app.include_router(ws_router)
