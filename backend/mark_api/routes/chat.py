import uuid

from fastapi import APIRouter, BackgroundTasks, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from mark_core.auth import get_current_user
from mark_core.db import SessionLocal, get_db
from mark_core.events import publish_ws
from mark_core.models import Message, Session, User
from mark_core.tasks import create_task, feed
from mark_core.worker import process_task

router = APIRouter()


class ChatBody(BaseModel):
    content: str
    session_id: str | None = None
    new_chat: bool = False
    for_voice: bool = False
    client_message_id: str | None = None
    """When set, chat answers are grounded in this Operations task report."""
    task_id: str | None = None


class TaskSnapshot(BaseModel):
    task_id: str
    title: str
    status: str
    progress: float
    objective: str


class VisualizeSnapshot(BaseModel):
    id: str
    title: str
    html: str
    description: str = ""


class BriefingSourceSnapshot(BaseModel):
    title: str
    url: str
    snippet: str = ""


class BriefingImageSnapshot(BaseModel):
    url: str
    thumb_url: str | None = None
    title: str | None = None
    source_url: str | None = None


class BriefingMarketSnapshot(BaseModel):
    symbol: str | None = None
    name: str | None = None
    price: float | None = None
    currency: str | None = None
    change: float | None = None
    change_pct: float | None = None
    as_of: str | None = None
    market_state: str | None = None
    chart_url: str | None = None
    error: str | None = None


class BriefingSnapshot(BaseModel):
    id: str
    query: str
    title: str
    summary: str
    kind: str = "research"
    image_url: str | None = None
    image_source: str | None = None
    images: list[BriefingImageSnapshot] = []
    facts: list[str] = []
    sources: list[BriefingSourceSnapshot] = []
    market: BriefingMarketSnapshot | None = None


class ChatResponse(BaseModel):
    session_id: str
    task_id: str | None = None
    task: TaskSnapshot | None = None
    mode: str
    intent: str
    assistant_message_id: str | None = None
    assistant_content: str | None = None
    visualize: VisualizeSnapshot | None = None
    briefing: BriefingSnapshot | None = None


async def _run_quick_chat(
    user_id: str,
    session_id: str,
    user_message: str,
    assistant_msg_id: str,
    *,
    for_voice: bool = False,
    task_report_context: str = "",
) -> tuple[str, dict | None, dict | None]:
    from mark_agents.chat_reply import generate_chat_reply
    from mark_memory.service import search_memory, store_memory
    from mark_tools.mcp_host import list_mcp_tools
    from mark_tools.registry import TOOLS

    try:
        async with SessionLocal() as db:
            from sqlalchemy import select

            result = await db.execute(select(User).where(User.id == uuid.UUID(user_id)))
            user = result.scalar_one_or_none()
            if not user:
                return "MARK could not verify your user session.", None, None
            memories = await search_memory(db, user.id, user_message, limit=4)
            context = "\n".join(m.content for m in memories) if memories else ""

        tool_lines = [f"- {t.name}: {t.description}" for t in TOOLS.values()]
        tool_lines += [f"- {t['name']}: {t['description']}" for t in list_mcp_tools()]
        tools_context = "\n".join(tool_lines[:28]) if tool_lines else "None"

        reply = await generate_chat_reply(
            user_message,
            context,
            user_id=user_id,
            for_voice=for_voice,
            tools_context=tools_context,
            task_report_context=task_report_context,
        )
        text = reply.text

        delta_chunk = 48
        for i in range(0, len(text), delta_chunk):
            await publish_ws(
                user_id,
                "chat.delta",
                {"message_id": assistant_msg_id, "delta": text[i : i + delta_chunk]},
            )

        await publish_ws(
            user_id,
            "chat.message",
            {
                "message_id": assistant_msg_id,
                "role": "assistant",
                "content": text,
                "speak": False,
            },
        )

        async with SessionLocal() as db:
            from sqlalchemy import select

            result = await db.execute(select(User).where(User.id == uuid.UUID(user_id)))
            user = result.scalar_one_or_none()
            if user:
                db.add(
                    Message(
                        id=uuid.UUID(assistant_msg_id),
                        session_id=uuid.UUID(session_id),
                        role="assistant",
                        content=text,
                    )
                )
                await store_memory(
                    db,
                    user.id,
                    "episodic",
                    f"User: {user_message[:300]}\n\nMARK: {text[:600]}",
                    scope="chat",
                    metadata={"session_id": session_id, "type": "chat_turn"},
                )
                await db.commit()
        return text, reply.visualize, reply.briefing
    except Exception as e:
        err = f"**Chat error:** {e}"
        await publish_ws(
            user_id,
            "chat.message",
            {"message_id": assistant_msg_id, "role": "assistant", "content": err, "speak": False},
        )
        return err, None, None


@router.post("/chat", response_model=ChatResponse)
async def chat(
    body: ChatBody,
    background_tasks: BackgroundTasks,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if body.new_chat or not body.session_id:
        session_id = uuid.uuid4()
        db.add(Session(id=session_id, user_id=user.id, title=body.content[:80]))
    else:
        session_id = uuid.UUID(body.session_id)
        existing = await db.get(Session, session_id)
        if not existing or existing.user_id != user.id:
            session_id = uuid.uuid4()
            db.add(Session(id=session_id, user_id=user.id, title=body.content[:80]))
    try:
        user_msg_id = (
            uuid.UUID(body.client_message_id) if body.client_message_id else uuid.uuid4()
        )
    except ValueError:
        user_msg_id = uuid.uuid4()

    db.add(
        Message(
            id=user_msg_id,
            session_id=session_id,
            role="user",
            content=body.content,
        )
    )
    await db.flush()

    await publish_ws(
        str(user.id),
        "chat.message",
        {"message_id": str(user_msg_id), "role": "user", "content": body.content},
    )

    from mark_agents.intent import classify_intent, generate_task_ack, is_skill_chat_request
    from mark_agents.request_router import route_request
    from mark_agents.task_report_context import is_task_report_question
    from mark_core.task_reports import format_report_for_prompt, resolve_report

    task_report_ctx = ""
    if body.task_id or is_task_report_question(body.content):
        report = await resolve_report(db, str(user.id), body.task_id)
        if report:
            task_report_ctx = format_report_for_prompt(report)

    plan = await route_request(body.content, use_llm=False)
    if (
        is_skill_chat_request(body.content)
        or plan.kind != "llm"
        or plan.intent == "chat"
        or task_report_ctx
        or is_task_report_question(body.content)
    ):
        intent = "chat"
    else:
        intent = await classify_intent(body.content)
    await publish_ws(
        str(user.id),
        "chat.intent",
        {"intent": intent, "session_id": str(session_id)},
    )

    if intent == "task":
        ack_text = await generate_task_ack(body.content, for_voice=body.for_voice)
        ack_id = uuid.uuid4()
        db.add(
            Message(
                id=ack_id,
                session_id=session_id,
                role="assistant",
                content=ack_text,
            )
        )
        await publish_ws(
            str(user.id),
            "chat.message",
            {
                "message_id": str(ack_id),
                "role": "assistant",
                "content": ack_text,
                "speak": False,
            },
        )

        title = body.content[:120] if len(body.content) > 120 else body.content
        task = await create_task(
            db,
            user,
            title=title or "User request",
            objective=body.content,
            session_id=session_id,
            enqueue=False,
        )
        await feed(str(user.id), str(task.id), "Task queued for autonomous execution.")
        await db.commit()
        background_tasks.add_task(process_task, str(task.id), str(user.id))
        snapshot = TaskSnapshot(
            task_id=str(task.id),
            title=task.title,
            status=task.status.value,
            progress=task.progress,
            objective=task.objective,
        )
        return ChatResponse(
            session_id=str(session_id),
            task_id=str(task.id),
            task=snapshot,
            mode="task",
            intent="task",
            assistant_message_id=str(ack_id),
            assistant_content=ack_text,
        )

    assistant_msg_id = str(uuid.uuid4())
    await db.commit()
    assistant_content, viz_payload, briefing_payload = await _run_quick_chat(
        str(user.id),
        str(session_id),
        body.content,
        assistant_msg_id,
        for_voice=body.for_voice,
        task_report_context=task_report_ctx,
    )
    viz_snap = VisualizeSnapshot(**viz_payload) if viz_payload else None
    brief_snap = None
    if briefing_payload:
        sources = [
            BriefingSourceSnapshot(**s)
            for s in (briefing_payload.get("sources") or [])
            if isinstance(s, dict)
        ]
        images = [
            BriefingImageSnapshot(**img)
            for img in (briefing_payload.get("images") or [])
            if isinstance(img, dict) and img.get("url")
        ]
        market_raw = briefing_payload.get("market")
        market_snap = (
            BriefingMarketSnapshot(**market_raw)
            if isinstance(market_raw, dict) and market_raw
            else None
        )
        brief_snap = BriefingSnapshot(
            id=briefing_payload.get("id", ""),
            query=briefing_payload.get("query", ""),
            title=briefing_payload.get("title", ""),
            summary=briefing_payload.get("summary", ""),
            kind=str(briefing_payload.get("kind") or "research"),
            image_url=briefing_payload.get("image_url"),
            image_source=briefing_payload.get("image_source"),
            images=images,
            facts=list(briefing_payload.get("facts") or []),
            sources=sources,
            market=market_snap,
        )
    return ChatResponse(
        session_id=str(session_id),
        task_id=None,
        mode="chat",
        intent="chat",
        assistant_message_id=assistant_msg_id,
        assistant_content=assistant_content,
        visualize=viz_snap,
        briefing=brief_snap,
    )
