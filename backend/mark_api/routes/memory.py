import hashlib
import uuid

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from mark_core.auth import get_current_user
from mark_core.db import get_db
from mark_core.models import User
from mark_memory.service import delete_memory, list_memory, store_memory

router = APIRouter()

CATEGORY_COLORS = {
    "semantic": "#6a8ab5",
    "episodic": "#7a8cb8",
    "procedural": "#5a7a9a",
    "project": "#8a9bb5",
    "agent": "#4a6d94",
    "credential": "#9a7a6a",
}


class MemoryResponse(BaseModel):
    id: str
    category: str
    scope: str
    content: str
    project_id: str | None
    created_at: str


class MemoryCreate(BaseModel):
    category: str
    content: str
    scope: str = "user"
    project_id: str | None = None
    label: str | None = None


class GraphNode(BaseModel):
    id: str
    label: str
    category: str
    color: str
    size: float
    content: str


class GraphLink(BaseModel):
    source: str
    target: str


class MemoryGraphResponse(BaseModel):
    nodes: list[GraphNode]
    links: list[GraphLink]


@router.get("/graph", response_model=MemoryGraphResponse)
async def memory_graph(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    records = await list_memory(db, user.id)

    nodes: list[GraphNode] = []
    links: list[GraphLink] = []
    hub_id = "mark-core"
    nodes.append(
        GraphNode(
            id=hub_id,
            label="MARK Core",
            category="semantic",
            color="#ffffff",
            size=12,
            content="Central knowledge nucleus",
        )
    )

    by_category: dict[str, list] = {}
    for r in records:
        cat = r.category.value
        by_category.setdefault(cat, []).append(r)
        label = r.content[:48] + ("…" if len(r.content) > 48 else "")
        nodes.append(
            GraphNode(
                id=str(r.id),
                label=label,
                category=cat,
                color=CATEGORY_COLORS.get(cat, "#6b7280"),
                size=4 + min(len(r.content) / 80, 8),
                content=r.content,
            )
        )
        links.append(GraphLink(source=hub_id, target=str(r.id)))

    # Intra-category links (memory clusters like reference graph)
    for cat, group in by_category.items():
        ids = [str(r.id) for r in group]
        for i in range(len(ids)):
            for j in range(i + 1, min(i + 3, len(ids))):
                links.append(GraphLink(source=ids[i], target=ids[j]))

    # Cross-links by content hash similarity (lightweight)
    for i, a in enumerate(records):
        for b in records[i + 1 : i + 4]:
            ha = hashlib.md5(a.content[:40].encode()).hexdigest()[:4]
            hb = hashlib.md5(b.content[:40].encode()).hexdigest()[:4]
            if ha == hb or a.category == b.category:
                links.append(GraphLink(source=str(a.id), target=str(b.id)))

    return MemoryGraphResponse(nodes=nodes, links=links)


@router.get("", response_model=list[MemoryResponse])
async def get_memory(
    category: str | None = Query(None),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    records = await list_memory(db, user.id, category)
    return [
        MemoryResponse(
            id=str(r.id),
            category=r.category.value,
            scope=r.scope,
            content=r.content,
            project_id=str(r.project_id) if r.project_id else None,
            created_at=r.created_at.isoformat(),
        )
        for r in records
    ]


@router.post("", response_model=MemoryResponse)
async def post_memory(
    body: MemoryCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    meta = {"label": body.label} if body.label else {}
    record = await store_memory(
        db,
        user.id,
        body.category,
        body.content,
        body.scope,
        project_id=body.project_id,
        metadata=meta,
    )
    return MemoryResponse(
        id=str(record.id),
        category=record.category.value,
        scope=record.scope,
        content=record.content,
        project_id=str(record.project_id) if record.project_id else None,
        created_at=record.created_at.isoformat(),
    )


@router.delete("/{memory_id}")
async def remove_memory(
    memory_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    ok = await delete_memory(db, user.id, uuid.UUID(memory_id))
    if not ok:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="Memory not found")
    return {"ok": True}
