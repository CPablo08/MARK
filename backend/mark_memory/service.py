import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from mark_core.models import MemoryCategory, MemoryRecord
from mark_memory.embeddings import embed_text
from mark_memory.qdrant_client import COLLECTION, ensure_collection, get_qdrant


async def store_memory(
    db: AsyncSession,
    user_id: uuid.UUID,
    category: str,
    content: str,
    scope: str = "user",
    task_id: str | None = None,
    project_id: str | None = None,
    metadata: dict | None = None,
) -> MemoryRecord:
    meta: dict = dict(metadata or {})
    if task_id:
        meta["task_id"] = task_id
    record = MemoryRecord(
        user_id=user_id,
        category=MemoryCategory(category),
        scope=scope,
        content=content,
        project_id=uuid.UUID(project_id) if project_id else None,
        metadata_json=meta,
    )
    db.add(record)
    await db.flush()

    try:
        ensure_collection()
        vector = await embed_text(content)
        point_id = str(record.id)
        get_qdrant().upsert(
            collection_name=COLLECTION,
            points=[
                {
                    "id": point_id,
                    "vector": vector,
                    "payload": {
                        "memory_id": point_id,
                        "category": category,
                        "scope": scope,
                        "user_id": str(user_id),
                        "task_id": task_id,
                    },
                }
            ],
        )
        record.embedding_id = point_id
        await db.flush()
    except Exception:
        pass

    return record


async def list_memory(
    db: AsyncSession, user_id: uuid.UUID, category: str | None = None
) -> list[MemoryRecord]:
    q = select(MemoryRecord).where(MemoryRecord.user_id == user_id)
    if category:
        q = q.where(MemoryRecord.category == MemoryCategory(category))
    result = await db.execute(q.order_by(MemoryRecord.created_at.desc()).limit(100))
    return list(result.scalars().all())


async def search_memory(
    db: AsyncSession, user_id: uuid.UUID, query: str, limit: int = 5
) -> list[MemoryRecord]:
    try:
        ensure_collection()
        vector = await embed_text(query)
        from qdrant_client.models import FieldCondition, Filter, MatchValue

        hits = get_qdrant().search(
            collection_name=COLLECTION,
            query_vector=vector,
            limit=limit,
            query_filter=Filter(
                must=[FieldCondition(key="user_id", match=MatchValue(value=str(user_id)))]
            ),
        )
        ids = [uuid.UUID(h.payload["memory_id"]) for h in hits if h.payload]
        if ids:
            result = await db.execute(select(MemoryRecord).where(MemoryRecord.id.in_(ids)))
            return list(result.scalars().all())
    except Exception:
        pass
    return await list_memory(db, user_id)


async def delete_memory(db: AsyncSession, user_id: uuid.UUID, memory_id: uuid.UUID) -> bool:
    result = await db.execute(
        select(MemoryRecord).where(
            MemoryRecord.id == memory_id,
            MemoryRecord.user_id == user_id,
        )
    )
    record = result.scalar_one_or_none()
    if not record:
        return False
    if record.embedding_id:
        try:
            get_qdrant().delete(collection_name=COLLECTION, points_selector=[record.embedding_id])
        except Exception:
            pass
    await db.delete(record)
    await db.flush()
    return True
