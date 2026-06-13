"""Execute routed briefing/visualize fast paths."""

from __future__ import annotations

from mark_agents.chat_result import ChatReplyResult
from mark_agents.request_router import RequestPlan
from mark_tools.visualize import clear_pending_visualization, open_visualization
from mark_tools.web_briefing import (
    build_image_briefing,
    build_market_briefing,
    build_web_briefing,
    open_web_briefing,
)
from mark_tools.visualize_templates import (
    generate_custom_visualization_html,
    newtons_cradle_html,
    parse_savings_defaults,
    savings_calculator_html,
)


def _briefing_reply(
    data: dict,
    payload: dict,
    *,
    for_voice: bool,
    user_id: str | None,
) -> ChatReplyResult:
    kind = data.get("kind", "research")
    n_img = len(data.get("images") or [])
    n_src = len(data.get("sources") or [])
    title = data.get("title", "Research")

    if for_voice:
        if kind == "market":
            text = f"Right — live quote for {title} is on screen. {(data.get('summary') or '')[:200]}"
        elif kind == "images":
            text = (
                f"I've loaded {n_img} images of {data.get('query', title)} in the center panel."
            )
        else:
            text = (
                f"I've opened {title} with {n_src} sources. "
                f"{(data.get('summary') or '')[:180]}"
            )
        return ChatReplyResult(text=text.strip(), briefing=payload)

    if kind == "market":
        text = f"**{title}** — live quote in the Research panel."
    elif kind == "images":
        text = f"**{n_img} images** for “{data.get('query', title)}” in the center panel."
    else:
        text = f"**{title}** — Research panel with **{n_src}** cited sources."
    if data.get("summary"):
        text += f"\n\n{data['summary'][:900]}"
    return ChatReplyResult(text=text, briefing=payload)


async def execute_routed_plan(
    plan: RequestPlan,
    user_message: str,
    *,
    user_id: str | None,
    for_voice: bool,
    memory_context: str = "",
) -> ChatReplyResult | None:
    if not user_id:
        return None

    if plan.kind == "market_briefing":
        data = await build_market_briefing(user_message, plan.symbol)
        payload = await open_web_briefing(user_id, data)
        clear_pending_visualization(user_id)
        return _briefing_reply(data, payload, for_voice=for_voice, user_id=user_id)

    if plan.kind == "image_briefing":
        data = await build_image_briefing(user_message)
        payload = await open_web_briefing(user_id, data)
        clear_pending_visualization(user_id)
        return _briefing_reply(data, payload, for_voice=for_voice, user_id=user_id)

    if plan.kind == "research_briefing":
        data = await build_web_briefing(user_message)
        payload = await open_web_briefing(user_id, data)
        clear_pending_visualization(user_id)
        return _briefing_reply(data, payload, for_voice=for_voice, user_id=user_id)

    if plan.kind == "newtons_cradle":
        payload = await open_visualization(
            user_id,
            title="Newton's Cradle",
            html=newtons_cradle_html(),
            description="Interactive physics demo.",
        )
        clear_pending_visualization(user_id)
        text = (
            "Newton's Cradle is in the center panel."
            if for_voice
            else "Opened **Newton's Cradle** in the center workspace."
        )
        return ChatReplyResult(text=text, visualize=payload)

    if plan.kind == "savings_calculator":
        defaults = parse_savings_defaults(user_message)
        html = savings_calculator_html(
            monthly=float(defaults["monthly"]),
            years=int(defaults["years"]),
            rate=float(defaults["rate"]),
        )
        payload = await open_visualization(
            user_id,
            title="Interactive Savings Calculator",
            html=html,
            description="Adjust sliders in the center panel.",
        )
        clear_pending_visualization(user_id)
        text = (
            "Savings calculator is up in the center."
            if for_voice
            else "Opened **savings calculator** in the center workspace."
        )
        return ChatReplyResult(text=text, visualize=payload)

    if plan.kind == "html_visualize":
        try:
            title, html = await generate_custom_visualization_html(
                user_message, context=memory_context
            )
            payload = await open_visualization(
                user_id,
                title=title,
                html=html,
                description="Interactive HTML workspace.",
            )
            clear_pending_visualization(user_id)
            text = (
                f"Opened {title} in the center."
                if for_voice
                else f"Opened **{title}** in the center workspace."
            )
            return ChatReplyResult(text=text, visualize=payload)
        except Exception:
            return None

    return None
