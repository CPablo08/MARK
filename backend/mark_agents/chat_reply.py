import uuid

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage

from mark_agents.briefing_handlers import execute_routed_plan
from mark_agents.cam_context import build_cam_context
from mark_agents.chat_result import ChatReplyResult
from mark_agents.education import academic_integrity_reply, is_academic_cheat_request
from mark_agents.capabilities import (
    CAPABILITIES_SYSTEM,
    capabilities_reply,
    is_capabilities_question,
)
from mark_agents.persona import (
    ARTIFACT_GROUNDING,
    JARVIS_CHAT_STYLE,
    JARVIS_VOICE_STYLE,
    ONLINE_CAPABILITIES,
    REPORT_QA_INSTRUCTION,
)
from mark_agents.chat_tools import build_chat_tools
from mark_agents.intent import is_cam_vision_question
from mark_agents.request_router import route_request
from mark_tools.visualize import pop_last_visualization
from mark_tools.web_briefing import pop_last_briefing
from mark_agents.llm import format_openrouter_error, get_llm
from mark_skills.cam import analyze_latest_frame, get_latest_frame
from mark_core.config import get_settings
from mark_tools.registry import TOOLS


def _finish(
    text: str,
    user_id: str | None,
    *,
    visualize: dict | None = None,
    briefing: dict | None = None,
) -> ChatReplyResult:
    return ChatReplyResult(text=text, visualize=visualize, briefing=briefing)


async def generate_chat_reply(
    user_message: str,
    memory_context: str = "",
    *,
    user_id: str | None = None,
    for_voice: bool = False,
    tools_context: str = "",
    task_report_context: str = "",
) -> ChatReplyResult:
    """Router → fast paths → tool loop → JARVIS reply with artifacts."""
    settings = get_settings()
    if not settings.openrouter_api_key:
        return _finish(
            "MARK is online, but OPENROUTER_API_KEY is missing in your env file. "
            "Add your key and restart the API to enable chat.",
            user_id,
        )

    if is_capabilities_question(user_message):
        return _finish(capabilities_reply(for_voice=for_voice), user_id)

    if is_academic_cheat_request(user_message):
        return _finish(academic_integrity_reply(for_voice=for_voice), user_id)

    plan = await route_request(user_message, use_llm=True)
    if user_id and plan.kind != "llm":
        routed = await execute_routed_plan(
            plan,
            user_message,
            user_id=user_id,
            for_voice=for_voice,
            memory_context=memory_context,
        )
        if routed:
            return routed

    if user_id and is_cam_vision_question(user_message):
        frame = get_latest_frame(user_id)
        if frame:
            analysis = await analyze_latest_frame(user_id, user_message)
            if for_voice:
                plain = analysis.replace("**", "").replace("*", "").replace("\n", " ")
                return _finish(plain[:500].strip() or analysis, user_id)
            return _finish(analysis, user_id)

    cam_ctx = build_cam_context(user_id) if user_id else ""
    style = JARVIS_VOICE_STYLE if for_voice else JARVIS_CHAT_STYLE

    report_block = ""
    if task_report_context.strip():
        report_block = f"\n\n{REPORT_QA_INSTRUCTION}\n\nLatest Operations report:\n{task_report_context}\n"

    tool_hint = ""
    if plan.suggested_tools:
        tool_hint = f"\nRouter suggests tools for this turn: {', '.join(plan.suggested_tools)}.\n"

    system = f"""You are MARK (Machine Augmented Reasoning and Knowledgebase) — a capable personal AI assistant.
{style}

{CAPABILITIES_SYSTEM}

{ONLINE_CAPABILITIES}
{ARTIFACT_GROUNDING}
{report_block}
{tool_hint}

Answer the user's actual question first. Do not pivot to GitHub unless they asked about GitHub.

You have tools — use them when appropriate:
- image_search: find pictures; pair with web_briefing for visual Research panel.
- web_search / web_research / browse_url: search and read the web headlessly.
- web_briefing: Research panel with image(s), summary, cited sources (who/what/tell me about).
- open_website: user's real browser tab.
- market_quote: live stock/index/crypto prices (use for tickers and indices).
- get_task_report / list_operations_reports: Ops reports.
- memory_remember / memory_search, github_*, visualize, cam_*, supervised tools, MCP.

Never claim a center panel opened unless you called web_briefing, visualize, or cam in this turn.
For pictures: call image_search then web_briefing, or web_briefing alone for topics.
Prefer one or two tool calls, then answer in character.

Registered tools:
{tools_context or "None"}

Relevant memory:
{memory_context or "None"}

Camera:
{cam_ctx or "Not active."}"""

    try:
        llm = get_llm("commander", temperature=0.42 if for_voice else 0.48)
        tools = []
        if user_id:
            try:
                tools = await build_chat_tools(uuid.UUID(user_id))
            except ValueError:
                tools = []

        if tools:
            llm = llm.bind_tools(tools)

        messages: list = [
            SystemMessage(content=system),
            HumanMessage(content=user_message),
        ]

        tool_map = {t.name: t for t in tools} if tools else {}
        max_rounds = 8
        opened_visualize = False
        opened_briefing = False

        for round_i in range(max_rounds):
            response: AIMessage = await llm.ainvoke(messages)
            if not getattr(response, "tool_calls", None):
                text = (response.content or "").strip()
                viz = pop_last_visualization(user_id) if user_id and opened_visualize else None
                brief = pop_last_briefing(user_id) if user_id and opened_briefing else None
                return _finish(
                    text or "I couldn't generate a reply.",
                    user_id,
                    visualize=viz,
                    briefing=brief,
                )

            messages.append(response)
            for call in response.tool_calls:
                name = call.get("name") if isinstance(call, dict) else call["name"]
                args = call.get("args") if isinstance(call, dict) else call["args"]
                call_id = call.get("id") if isinstance(call, dict) else call["id"]

                lc_tool = tool_map.get(name)
                if lc_tool:
                    try:
                        result = await lc_tool.ainvoke(args or {})
                    except Exception as e:
                        result = f"Tool error: {e}"
                elif name in TOOLS:
                    try:
                        raw = await TOOLS[name].handler(**(args or {}))
                        result = str(raw)
                    except Exception as e:
                        result = f"Tool error: {e}"
                else:
                    result = f"Unknown tool: {name}"

                if name == "visualize":
                    opened_visualize = True
                elif name in ("web_briefing", "image_search"):
                    if name == "web_briefing":
                        opened_briefing = True

                messages.append(
                    ToolMessage(content=str(result), tool_call_id=call_id or name)
                )

            if opened_briefing and round_i >= 1:
                break

            if round_i >= max_rounds - 1:
                break

        final_response: AIMessage = await llm.ainvoke(messages)
        viz = pop_last_visualization(user_id) if user_id and opened_visualize else None
        brief = pop_last_briefing(user_id) if user_id and opened_briefing else None
        if final_response.content:
            return _finish(str(final_response.content).strip(), user_id, visualize=viz, briefing=brief)
        return _finish(
            "I couldn't phrase a reply — please ask again.",
            user_id,
            visualize=viz,
            briefing=brief,
        )

    except Exception as e:
        return _finish(format_openrouter_error(e), user_id)
