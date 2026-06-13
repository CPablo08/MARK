"""LangChain tools available during quick chat."""

import uuid

from langchain_core.tools import StructuredTool
from sqlalchemy import select

from mark_core.db import SessionLocal
from mark_core.models import User
from mark_memory.service import search_memory, store_memory
from mark_tools import browser as web
from mark_tools.open_browser import open_in_user_browser
from mark_tools.image_search import image_search_text
from mark_tools.web_briefing import (
    build_image_briefing,
    build_market_briefing,
    build_web_briefing,
    is_image_briefing_request,
    open_web_briefing,
)
from mark_agents.request_router import is_market_request, route_request_rules
from mark_core.task_reports import format_report_for_prompt, list_cached_reports, resolve_report
from mark_tools import github as gh
from mark_tools import market as market_tools
from mark_core.safety import request_chat_approval, wait_until_approval_resolved
from mark_skills.cam import analyze_latest_frame, close_cam_skill, open_cam_skill
from mark_tools import supervised_actions as supervised
from mark_tools.mcp_host import build_mcp_langchain_tools
from mark_tools.visualize import close_visualization, open_visualization

_USER_ID: uuid.UUID | None = None


async def _supervised_gate(
    user_id: uuid.UUID,
    action: str,
    description: str,
    payload: dict,
    run,
) -> str:
    """Request in-app approval, wait for user, then run the action."""
    async with SessionLocal() as db:
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            return "User not found."
        approval = await request_chat_approval(db, user, action, description, payload)
        await db.commit()
        approval_id = approval.id

    status = await wait_until_approval_resolved(approval_id)
    if status == "timeout":
        return "Approval timed out (10 minutes). Ask the user to try again."
    if status == "denied":
        return "User denied this action in MARK."

    return await run()


async def build_chat_tools(user_id: uuid.UUID) -> list[StructuredTool]:
    global _USER_ID
    _USER_ID = user_id
    uid = str(user_id)
    async def github_account() -> str:
        """Return the GitHub username and profile for the token in .env."""
        try:
            return await gh.get_authenticated_user()
        except ValueError as e:
            return str(e)
        except Exception as e:
            return f"GitHub error: {e}"

    async def github_list_repos() -> str:
        """List GitHub repositories accessible to the configured token."""
        try:
            return await gh.list_repositories()
        except ValueError as e:
            return str(e)
        except Exception as e:
            return f"GitHub error: {e}"

    async def web_search(query: str, max_results: int = 5) -> str:
        """Search the public web (DuckDuckGo). Returns titles, URLs, snippets."""
        try:
            return await web.web_search(query, max_results=max_results)
        except Exception as e:
            return f"Web search error: {e}"

    async def browse_url(url: str) -> str:
        """Fetch a URL headlessly (Playwright) and return readable page text — does not open your GUI browser."""
        try:
            return await web.browse_url(url)
        except Exception as e:
            return f"Browse error: {e}"

    async def open_website(url: str) -> str:
        """Open a URL in the user's default web browser (Safari, Chrome, etc.) on their computer."""
        try:
            return await open_in_user_browser(url)
        except Exception as e:
            return f"Could not open browser: {e}"

    async def get_task_report(task_id: str = "") -> str:
        """Load an Operations task report by ID, or the most recent if ID omitted."""
        try:
            async with SessionLocal() as db:
                report = await resolve_report(
                    db, uid, task_id.strip() or None
                )
            if not report:
                return "No Operations report found. Complete a task in Ops first, or pass a task_id."
            return format_report_for_prompt(report, max_chars=8000)
        except Exception as e:
            return f"Could not load report: {e}"

    async def list_operations_reports() -> str:
        """List recent completed Operations tasks (for follow-up questions)."""
        rows = list_cached_reports(uid, limit=8)
        if not rows:
            return "No recent Operations reports in cache."
        lines = []
        for r in rows:
            lines.append(
                f"- {r.get('title')} [{r.get('status')}] id={r.get('task_id')} "
                f"preview: {(r.get('result_preview') or '')[:100]}"
            )
        return "Recent Operations reports:\n" + "\n".join(lines)

    async def web_research(query: str) -> str:
        """Search the web and read the most relevant top result."""
        try:
            return await web.web_research(query)
        except Exception as e:
            return f"Web research error: {e}"

    async def image_search(query: str, max_results: int = 8) -> str:
        """Search the web for images (Playwright). Returns URLs for the Research gallery."""
        try:
            return await image_search_text(query, max_results=max_results)
        except Exception as e:
            return f"Image search error: {e}"

    async def web_briefing(query: str) -> str:
        """Open the center Research panel with image(s), summary, and cited sources."""
        try:
            if is_market_request(query):
                sym = route_request_rules(query).symbol
                data = await build_market_briefing(query, sym)
            elif is_image_briefing_request(query):
                data = await build_image_briefing(query)
            else:
                data = await build_web_briefing(query)
            await open_web_briefing(uid, data)
            n_img = len(data.get("images") or [])
            n = len(data.get("sources") or [])
            return (
                f"Research panel open ({data.get('kind', 'research')}) for “{data.get('title')}” "
                f"with {n_img} images and {n} sources. Summarize briefly; user sees the center panel."
            )
        except Exception as e:
            return f"Briefing error: {e}"

    async def market_quote(symbol: str = "^GSPC") -> str:
        """Get a live or recent market quote (stocks, indices, crypto)."""
        try:
            return await market_tools.get_market_quote(symbol)
        except Exception as e:
            return f"Market quote error: {e}"

    async def memory_search(query: str) -> str:
        """Search the user's memory vault for relevant notes."""
        async with SessionLocal() as db:
            uid = user_id
            result = await db.execute(select(User).where(User.id == uid))
            if not result.scalar_one_or_none():
                return "User not found."
            records = await search_memory(db, uid, query, limit=6)
        if not records:
            return "No matching memories."
        return "\n".join(f"- [{m.category.value}] {m.content[:200]}" for m in records)

    async def memory_remember(
        content: str,
        category: str = "semantic",
        label: str = "",
    ) -> str:
        """Save a fact, preference, or credential reference to the memory vault."""
        allowed = {"semantic", "episodic", "procedural", "project", "credential", "agent"}
        cat = category if category in allowed else "semantic"
        text = content.strip()
        if not text:
            return "Nothing to save — content was empty."
        if len(text) > 4000:
            text = text[:4000]
        async with SessionLocal() as db:
            result = await db.execute(select(User).where(User.id == user_id))
            user = result.scalar_one_or_none()
            if not user:
                return "User not found."
            meta = {"label": label} if label.strip() else {}
            await store_memory(
                db,
                user_id,
                cat,
                text,
                scope="vault",
                metadata=meta,
            )
            await db.commit()
        return f"Saved to vault ({cat})."

    async def visualize(
        title: str,
        html: str,
        description: str = "",
    ) -> str:
        """Open an interactive HTML visualization in the center workspace (not in chat).

        Use for charts, income projections, dashboards, calculators, diagrams, or any rich UI.
        Provide a complete HTML document or fragment with inline CSS/JS (Chart.js from cdn.jsdelivr.net is fine).
        Do NOT paste the full HTML in the chat — only a short summary for the user.
        """
        await open_visualization(
            uid,
            title=title,
            html=html,
            description=description,
        )
        return (
            f"Visualization '{title}' is now open in the center workspace panel. "
            "Give a brief spoken summary; the user sees the interactive view in the middle of the app."
        )

    async def visualize_close() -> str:
        """Close the center visualization panel."""
        await close_visualization(uid)
        return "Visualization panel closed."

    async def cam(objective: str = "Observe and describe the scene") -> str:
        """Open the Cam skill: live camera with on-device object detection in the center panel.

        Chat collapses to the bottom while Cam is active. Use for seeing the room, objects, people, etc.
        Follow up with cam_analyze once the camera has had a moment to capture frames.
        """
        await open_cam_skill(uid, objective)
        return (
            f"Cam skill active — objective: {objective}. "
            "The user sees live camera + CV overlay in the center. "
            "Use cam_analyze(question) to interpret the latest frame. Use cam_close when done."
        )

    async def cam_analyze(question: str) -> str:
        """Analyze the latest camera frame (vision + local detections). Requires cam skill to be open."""
        return await analyze_latest_frame(uid, question)

    async def cam_close() -> str:
        """Close the Cam skill and restore the normal layout."""
        await close_cam_skill(uid)
        return "Cam skill closed."

    async def run_terminal_command(command: str, cwd: str = "") -> str:
        """Run a shell command on the user's machine (sandbox by default). Requires approval."""

        async def _run() -> str:
            return await supervised.run_terminal_command(
                command, cwd=cwd or None, timeout_sec=120
            )

        return await _supervised_gate(
            user_id,
            "terminal",
            f"Run shell command:\n{command[:500]}",
            {"command": command, "cwd": cwd},
            _run,
        )

    async def send_email(to: str, subject: str, body: str) -> str:
        """Send an email via SMTP. Requires explicit user approval in MARK."""

        async def _run() -> str:
            return await supervised.send_email(to, subject, body)

        return await _supervised_gate(
            user_id,
            "email",
            f"Send email to {to}\nSubject: {subject}\n\n{body[:800]}",
            {"to": to, "subject": subject, "body": body},
            _run,
        )

    async def send_sms(to: str, body: str) -> str:
        """Send SMS via Twilio. Requires approval."""

        async def _run() -> str:
            return await supervised.send_sms_via_twilio(to, body)

        return await _supervised_gate(
            user_id,
            "sms",
            f"Send SMS to {to}:\n{body[:500]}",
            {"to": to, "body": body},
            _run,
        )

    async def place_phone_call(to: str, purpose: str = "") -> str:
        """Place outbound voice call via Twilio. Requires approval."""

        async def _run() -> str:
            return await supervised.start_voice_call_twilio(to)

        return await _supervised_gate(
            user_id,
            "phone_call",
            f"Call {to}" + (f" — {purpose}" if purpose else ""),
            {"to": to, "purpose": purpose},
            _run,
        )

    async def travel_booking_assist(
        origin: str,
        destination: str,
        depart_date: str,
        return_date: str = "",
        notes: str = "",
    ) -> str:
        """Search flight options on the web. Does NOT purchase — user completes booking."""

        query = (
            f"flights {origin} to {destination} {depart_date}"
            + (f" return {return_date}" if return_date else "")
            + (f" {notes}" if notes else "")
        )
        try:
            search = await web.web_search(query, max_results=6)
            return (
                f"**Flight search (no purchase made)**\n\n{search}\n\n"
                "Tell the user to open the airline or travel site link to book. "
                "Offer to draft a confirmation email after they book."
            )
        except Exception as e:
            return f"Travel search failed: {e}"

    tools: list[StructuredTool] = [
        StructuredTool.from_function(
            coroutine=github_account,
            name="github_account",
            description="Get the GitHub account linked via GITHUB_TOKEN (login, name, public repo count).",
        ),
        StructuredTool.from_function(
            coroutine=github_list_repos,
            name="github_list_repos",
            description="List all GitHub repositories the token can access. Use when asked about repos.",
        ),
        StructuredTool.from_function(
            coroutine=web_search,
            name="web_search",
            description=(
                "Search the web for current information, news, prices, or facts. "
                "Use for anything needing up-to-date data beyond market_quote tickers."
            ),
        ),
        StructuredTool.from_function(
            coroutine=browse_url,
            name="browse_url",
            description=(
                "Read a URL headlessly and return page text (Playwright). "
                "Does NOT open the user's GUI browser — use open_website for that."
            ),
        ),
        StructuredTool.from_function(
            coroutine=open_website,
            name="open_website",
            description=(
                "Open a URL in the user's default system browser (Safari, Chrome, Firefox). "
                "Use when they say 'open in my browser', 'go to this site', or want to see a page themselves. "
                "For reading content without opening a tab, use browse_url instead."
            ),
        ),
        StructuredTool.from_function(
            coroutine=get_task_report,
            name="get_task_report",
            description=(
                "Load a completed Operations / MARK task report. Use when user asks about "
                "the report, findings, or wants interpretation. Empty task_id = latest report."
            ),
        ),
        StructuredTool.from_function(
            coroutine=list_operations_reports,
            name="list_operations_reports",
            description="List recent Operations task reports with task IDs.",
        ),
        StructuredTool.from_function(
            coroutine=web_research,
            name="web_research",
            description="Search the web and read the top hit — best for broad current-events questions.",
        ),
        StructuredTool.from_function(
            coroutine=image_search,
            name="image_search",
            description=(
                "Find images on the web (returns URLs). Use before web_briefing when user wants pictures."
            ),
        ),
        StructuredTool.from_function(
            coroutine=web_briefing,
            name="web_briefing",
            description=(
                "Open center Research panel with image gallery, summary, and cited sources. "
                "Use for who/what is X, pictures, market quotes, tell me about X."
            ),
        ),
        StructuredTool.from_function(
            coroutine=market_quote,
            name="market_quote",
            description=(
                "Get current/recent price for a ticker or index. Use for stock/crypto/index questions. "
                "Examples: ^GSPC or 'S&P 500', AAPL, TSLA, BTC-USD, ^IXIC. Defaults to S&P 500."
            ),
        ),
        StructuredTool.from_function(
            coroutine=memory_search,
            name="memory_search",
            description="Search stored memories for context relevant to the user's question.",
        ),
        StructuredTool.from_function(
            coroutine=memory_remember,
            name="memory_remember",
            description=(
                "Save information to the vault for later. Use when the user shares their name, "
                "preferences, facts about themselves, or asks you to remember something. "
                "category: semantic (facts), credential (login references — never store raw passwords "
                "unless the user explicitly provides them for vault storage), episodic (events)."
            ),
        ),
        StructuredTool.from_function(
            coroutine=visualize,
            name="visualize",
            description=(
                "Visualize plugin: render HTML/interactive charts in the CENTER workspace panel "
                "(like Claude artifacts). Use for projections, graphs, tables, calculators. "
                "Pass complete html. Never dump raw HTML in chat."
            ),
        ),
        StructuredTool.from_function(
            coroutine=visualize_close,
            name="visualize_close",
            description="Close the center visualization workspace.",
        ),
        StructuredTool.from_function(
            coroutine=cam,
            name="cam",
            description=(
                "Cam skill: open live camera + CV detection in center panel; chat collapses at bottom. "
                "Use when the user wants to see/analyze the physical world via webcam."
            ),
        ),
        StructuredTool.from_function(
            coroutine=cam_analyze,
            name="cam_analyze",
            description="Ask a question about the latest camera frame (after cam is open).",
        ),
        StructuredTool.from_function(
            coroutine=cam_close,
            name="cam_close",
            description="Close the Cam skill and restore normal UI.",
        ),
        StructuredTool.from_function(
            coroutine=run_terminal_command,
            name="run_terminal_command",
            description=(
                "Run a shell command on the user's computer (sandbox cwd). "
                "BLOCKED until user taps Approve in MARK. Never sudo or destructive commands."
            ),
        ),
        StructuredTool.from_function(
            coroutine=send_email,
            name="send_email",
            description=(
                "Send email via SMTP. BLOCKED until user approves. Show draft in approval dialog."
            ),
        ),
        StructuredTool.from_function(
            coroutine=send_sms,
            name="send_sms",
            description="Send SMS (Twilio). Requires user approval in MARK.",
        ),
        StructuredTool.from_function(
            coroutine=place_phone_call,
            name="place_phone_call",
            description="Outbound phone call (Twilio). Requires user approval.",
        ),
        StructuredTool.from_function(
            coroutine=travel_booking_assist,
            name="travel_booking_assist",
            description=(
                "Search/compare flights (web). Does not book tickets — user books on airline site."
            ),
        ),
    ]
    tools.extend(build_mcp_langchain_tools())
    return tools
