"""Background worker: consumes task queue and runs Commander orchestration."""
import asyncio
import logging
import uuid

from sqlalchemy import select

from mark_core.config import get_settings
from mark_core.db import SessionLocal
from mark_core.events import get_redis, publish_ws
from mark_core.models import Task, TaskStatus, User
from mark_core.tasks import TASK_QUEUE, feed, update_task_status

logger = logging.getLogger("mark.worker")
settings = get_settings()


async def process_task(task_id: str, user_id: str) -> None:
    from mark_agents.commander import run_commander

    async with SessionLocal() as db:
        result = await db.execute(select(Task).where(Task.id == uuid.UUID(task_id)))
        task = result.scalar_one_or_none()
        if not task:
            return

        user_result = await db.execute(select(User).where(User.id == uuid.UUID(user_id)))
        user = user_result.scalar_one_or_none()
        if not user:
            return

        await update_task_status(db, task, TaskStatus.running, 5.0)
        await db.commit()
        await feed(user_id, task_id, f"Commander engaged: {task.title}")

        try:
            result = await run_commander(db, user, task)
            await update_task_status(
                db, task, TaskStatus.completed, 100.0, result=result
            )
            await db.commit()
            await feed(user_id, task_id, "Task completed successfully.")
        except Exception as e:
            logger.exception("Task failed: %s", task_id)
            err_result = {
                "result_kind": "error",
                "result_preview": str(e)[:200],
                "result_content": f"**Task failed**\n\n{e}",
            }
            await update_task_status(
                db, task, TaskStatus.failed, task.progress, result=err_result
            )
            await db.commit()
            await feed(user_id, task_id, f"Task failed: {e}", "error")
        await db.commit()


async def worker_loop() -> None:
    logger.info("MARK worker started")
    r = await get_redis()
    if not r:
        logger.warning("Redis unavailable — tasks run inline via API")
        while True:
            await asyncio.sleep(60)
        return
    while True:
        try:
            item = await r.brpop(TASK_QUEUE, timeout=5)
            if not item:
                continue
            _, raw = item
            task_id, user_id = raw.split(":", 1)
            await process_task(task_id, user_id)
        except Exception:
            logger.exception("Worker loop error")
            await asyncio.sleep(2)


async def publish_metrics_loop() -> None:
    while True:
        try:
            r = await get_redis()
            depth = await r.llen(TASK_QUEUE)
            # broadcast to all connected users via global channel pattern
            await r.publish(
                "mark:metrics",
                '{"type":"metrics.snapshot","payload":{"active_agents":0,"queue_depth":'
                + str(depth)
                + ',"tokens_used":0,"system_health":"healthy"}}',
            )
        except Exception:
            pass
        await asyncio.sleep(10)


def main() -> None:
    logging.basicConfig(level=logging.INFO)

    async def run() -> None:
        await asyncio.gather(worker_loop(), publish_metrics_loop())

    asyncio.run(run())


if __name__ == "__main__":
    main()
