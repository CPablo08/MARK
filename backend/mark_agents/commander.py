import re
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from mark_agents.roles.browser import run_browser_agent
from mark_agents.task_result import infer_result_kind, preview_text
from mark_agents.roles.coding import run_coding_agent
from mark_agents.roles.memory_agent import run_memory_agent
from mark_agents.roles.planner import run_planner_agent
from mark_agents.roles.research import run_research_agent
from mark_agents.roles.verification import run_verification_agent
from mark_core.events import publish_ws
from mark_core.models import Agent, AuditLog, Message, Task, TaskStatus, User
from mark_core.tasks import emit_agent_status, feed, update_task_status
from mark_memory.service import search_memory, store_memory

_RESEARCH = re.compile(
    r"\b(research|analyze|analyse|investigate|probability|forecast|outlook|"
    r"compare|study|assessment|risk|investment|market outlook)\b",
    re.I,
)
_CODE = re.compile(
    r"\b(build|code|implement|deploy|refactor|scaffold|repository|api endpoint|"
    r"write a script|full stack|next\.?js|react app)\b",
    re.I,
)


def _is_research_task(objective: str) -> bool:
    return bool(_RESEARCH.search(objective)) and not bool(_CODE.search(objective))


async def spawn_agent(
    db: AsyncSession, user: User, task: Task, role: str
) -> Agent:
    agent = Agent(user_id=user.id, task_id=task.id, role=role, status="running")
    db.add(agent)
    await db.flush()
    await emit_agent_status(str(user.id), str(agent.id), role, "running", str(task.id))
    return agent


async def _finish_agent(db: AsyncSession, user_id: str, agent: Agent, task_id: str) -> None:
    agent.status = "completed"
    await emit_agent_status(user_id, str(agent.id), agent.role, "completed", task_id)


async def _step(
    db: AsyncSession,
    user: User,
    task: Task,
    progress: float,
    line: str,
) -> None:
    await feed(str(user.id), str(task.id), line)
    await update_task_status(db, task, TaskStatus.running, progress)
    await db.commit()


async def _publish_report(
    db: AsyncSession,
    user_id: str,
    task: Task,
    response: str,
    *,
    research_mode: bool,
) -> dict:
    assistant_msg_id = uuid.uuid4()
    if task.session_id:
        db.add(
            Message(
                id=assistant_msg_id,
                session_id=task.session_id,
                role="assistant",
                content=response,
                metadata_json={"task_id": str(task.id), "type": "task_result"},
            )
        )
        await db.flush()

    msg_id = str(assistant_msg_id)
    delta_chunk = 80
    for i in range(0, len(response), delta_chunk):
        await publish_ws(
            user_id,
            "chat.delta",
            {"message_id": msg_id, "delta": response[i : i + delta_chunk]},
        )
    await publish_ws(
        user_id,
        "chat.message",
        {
            "message_id": msg_id,
            "role": "assistant",
            "content": response,
            "task_id": str(task.id),
            "result_kind": infer_result_kind(response, research_mode=research_mode),
        },
    )

    kind = infer_result_kind(response, research_mode=research_mode)
    return {
        "result_message_id": msg_id,
        "result_kind": kind,
        "result_preview": preview_text(response),
        "result_content": response,
    }


async def run_commander(db: AsyncSession, user: User, task: Task) -> dict:
    from mark_agents.intent import is_cam_skill_request, is_visualize_request
    from mark_skills.cam import open_cam_skill
    from mark_tools.visualize import open_visualization
    from mark_tools.visualize_templates import (
        generate_custom_visualization_html,
        is_html_visualize_request,
        is_savings_calculator_request,
        parse_savings_defaults,
        savings_calculator_html,
    )

    user_id = str(user.id)
    task_id = str(task.id)

    if is_html_visualize_request(task.objective) and not is_savings_calculator_request(
        task.objective
    ):
        await feed(user_id, task_id, "Generating HTML visualization…")
        await update_task_status(db, task, TaskStatus.running, 50.0)
        await db.commit()
        title, html = await generate_custom_visualization_html(task.objective)
        await open_visualization(
            user_id,
            title=title,
            html=html,
            description="Generated for the center workspace panel.",
        )
        report = (
            f"Opened **{title}** in the center workspace. "
            "This is interactive HTML in the app — not a separate file or Operations job."
        )
        return await _publish_report(db, user_id, task, report, research_mode=False)

    if is_savings_calculator_request(task.objective) or (
        is_visualize_request(task.objective)
        and re.search(r"\b(calculator|interactive|slider|adjust)\b", task.objective, re.I)
    ):
        await feed(user_id, task_id, "Opening interactive visualization in the app…")
        await update_task_status(db, task, TaskStatus.running, 50.0)
        await db.commit()
        defaults = parse_savings_defaults(task.objective)
        html = savings_calculator_html(
            monthly=float(defaults["monthly"]),
            years=int(defaults["years"]),
            rate=float(defaults["rate"]),
        )
        await open_visualization(
            user_id,
            title="Interactive Savings Calculator",
            html=html,
            description="Adjust parameters with the sliders.",
        )
        report = (
            "Opened an **interactive savings calculator** in the center workspace. "
            "Use the sliders — no Operations panel or external tools needed."
        )
        return await _publish_report(db, user_id, task, report, research_mode=False)

    # Misrouted skill requests should not run web research / OpenCV in the worker.
    if is_cam_skill_request(task.objective):
        await feed(user_id, task_id, "Opening Cam skill in the app…")
        await update_task_status(db, task, TaskStatus.running, 50.0)
        await db.commit()
        await open_cam_skill(user_id, task.objective)
        report = (
            "Opened the **Cam** skill in the center panel. "
            "Allow camera access when prompted — live video and object detection run in the browser."
        )
        return await _publish_report(db, user_id, task, report, research_mode=False)

    research_mode = _is_research_task(task.objective)

    await feed(user_id, task_id, "Commander analyzing objective...")
    await update_task_status(db, task, TaskStatus.running, 10.0)
    await db.commit()

    memories = await search_memory(db, user.id, task.objective, limit=5)
    context = "\n".join(m.content for m in memories) if memories else ""

    commander = await spawn_agent(db, user, task, "commander")
    planner = await spawn_agent(db, user, task, "planner")
    await db.commit()

    await _step(db, user, task, 18.0, "Planner decomposing objective...")
    plan = await run_planner_agent(task.objective, context)
    await _step(db, user, task, 28.0, f"Plan ready ({len(plan)} chars)")

    research_agent = await spawn_agent(db, user, task, "research")
    await db.commit()
    await _step(db, user, task, 40.0, "Research agent gathering sources...")
    research = await run_research_agent(task.objective, plan)
    await _step(db, user, task, 55.0, "Research synthesis complete")

    browser_agent = await spawn_agent(db, user, task, "browser")
    await db.commit()
    await _step(db, user, task, 65.0, "Browser agent reading top sources...")
    browser_result = await run_browser_agent(task.objective)
    await _step(db, user, task, 72.0, "Web verification complete")

    code_result = ""
    coding_agent = None
    if not research_mode:
        coding_agent = await spawn_agent(db, user, task, "coding")
        await db.commit()
        await _step(db, user, task, 78.0, "Coding agent generating artifacts...")
        code_result = await run_coding_agent(task.objective, plan)
        await _step(db, user, task, 85.0, "Code artifacts ready")

    verify_agent = await spawn_agent(db, user, task, "verification")
    await db.commit()
    await _step(db, user, task, 90.0, "Verification agent reviewing outputs...")
    verified = await run_verification_agent(task.objective, research, code_result or browser_result)
    await _step(db, user, task, 95.0, "Verification complete")

    memory_agent = await spawn_agent(db, user, task, "memory")
    await db.commit()
    summary = (
        f"Objective: {task.objective}\nPlan: {plan}\nResearch: {research[:500]}\n"
        f"Verified: {verified}"
    )
    await run_memory_agent(db, user.id, summary, task_id)
    await store_memory(db, user.id, "episodic", summary, "task", task_id)

    if research_mode:
        response = (
            f"**MARK Research — {task.title}**\n\n"
            f"{verified}\n\n"
            f"---\n"
            f"*Key findings:*\n{research[:1200]}"
            f"{'…' if len(research) > 1200 else ''}\n\n"
            f"*Sources reviewed:*\n{browser_result[:600]}"
            f"{'…' if len(browser_result) > 600 else ''}"
        )
    else:
        response = (
            f"**MARK Report — {task.title}**\n\n"
            f"{verified}\n\n"
            f"---\n"
            f"*Research excerpt:* {research[:400]}...\n\n"
            f"*Browser:* {browser_result}\n\n"
            f"*Code:* {code_result[:300]}..."
        )

    result = await _publish_report(
        db, user_id, task, response, research_mode=research_mode
    )

    agents = [commander, planner, research_agent, browser_agent, verify_agent, memory_agent]
    if coding_agent:
        agents.insert(4, coding_agent)
    for agent in agents:
        await _finish_agent(db, user_id, agent, task_id)

    db.add(
        AuditLog(
            user_id=user.id,
            action="task.completed",
            actor="commander",
            payload_json={"task_id": task_id, "title": task.title, "research_mode": research_mode},
        )
    )
    await feed(user_id, task_id, "Commander cycle complete.")
    await db.commit()
    return result
