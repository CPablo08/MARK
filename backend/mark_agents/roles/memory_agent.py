import uuid

from mark_memory.service import store_memory


async def run_memory_agent(db, user_id: uuid.UUID, summary: str, task_id: str) -> None:
    await store_memory(db, user_id, "semantic", summary[:2000], "agent", task_id)
    await store_memory(db, user_id, "procedural", f"Completed task {task_id}", "agent", task_id)
