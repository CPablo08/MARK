"""Priority routing: market > images > research > skills > LLM (+ optional micro-LLM)."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Literal

from mark_agents.intent import is_skill_chat_request
from mark_agents.llm import get_llm
from mark_core.config import get_settings
from mark_tools.visualize_templates import (
    is_html_visualize_request,
    is_newtons_cradle_request,
    is_savings_calculator_request,
)
from mark_tools.web_briefing import is_image_briefing_request, is_research_briefing_request

RouteKind = Literal[
    "llm",
    "market_briefing",
    "image_briefing",
    "research_briefing",
    "newtons_cradle",
    "savings_calculator",
    "html_visualize",
    "cam_vision",
]

_MARKET = re.compile(
    r"\b("
    r"stock|stocks|share price|market cap|ticker|trading at|"
    r"current price|price of|how much is|quote for|"
    r"s&p|sp\s*500|nasdaq|dow jones|bitcoin|btc|ethereum|eth|crypto"
    r")\b",
    re.I,
)
_MARKET_PRICE_LINE = re.compile(
    r"\b(current|live|today'?s?)\s+(price|value|quote)\b", re.I
)


@dataclass
class RequestPlan:
    kind: RouteKind = "llm"
    subject: str = ""
    symbol: str = ""
    suggested_tools: list[str] = field(default_factory=list)
    intent: Literal["chat", "task"] = "chat"
    artifact: Literal["none", "briefing", "visualize", "cam", "ops"] = "none"


def _extract_market_symbol(message: str) -> str:
    text = message.strip()
    m = re.search(r"\b(?:price of|quote for|ticker)\s+([A-Z0-9^.\-]+)", text, re.I)
    if m:
        return m.group(1)
    if re.search(r"s&p|sp\s*500", text, re.I):
        return "^GSPC"
    if re.search(r"\bnasdaq\b", text, re.I):
        return "^IXIC"
    if re.search(r"\bdow\b", text, re.I):
        return "^DJI"
    if re.search(r"\bbitcoin\b|\bbtc\b", text, re.I):
        return "BTC-USD"
    m = re.search(r"\b([A-Z]{1,5})\b", text)
    if m and m.group(1) not in ("THE", "AND", "FOR", "WHAT", "IS"):
        return m.group(1)
    return "^GSPC"


def is_market_request(message: str) -> bool:
    text = message.strip()
    if not text:
        return False
    if _MARKET.search(text):
        return True
    if _MARKET_PRICE_LINE.search(text) and re.search(
        r"\b(s&p|index|stock|nasdaq|dow|bitcoin|ticker)\b", text, re.I
    ):
        return True
    return False


def route_request_rules(message: str) -> RequestPlan:
    """Ordered rule-based router (fast, no LLM)."""
    text = message.strip()
    plan = RequestPlan(subject=text)

    if is_market_request(text):
        plan.kind = "market_briefing"
        plan.symbol = _extract_market_symbol(text)
        plan.suggested_tools = ["market_quote"]
        plan.artifact = "briefing"
        plan.intent = "chat"
        return plan

    if is_image_briefing_request(text):
        plan.kind = "image_briefing"
        plan.suggested_tools = ["image_search", "web_search"]
        plan.artifact = "briefing"
        plan.intent = "chat"
        return plan

    if is_research_briefing_request(text):
        plan.kind = "research_briefing"
        plan.suggested_tools = ["web_briefing"]
        plan.artifact = "briefing"
        plan.intent = "chat"
        return plan

    if is_newtons_cradle_request(text):
        plan.kind = "newtons_cradle"
        plan.artifact = "visualize"
        plan.intent = "chat"
        return plan

    if is_savings_calculator_request(text):
        plan.kind = "savings_calculator"
        plan.artifact = "visualize"
        plan.intent = "chat"
        return plan

    if is_html_visualize_request(text) and not is_savings_calculator_request(text):
        plan.kind = "html_visualize"
        plan.artifact = "visualize"
        plan.intent = "chat"
        return plan

    if is_skill_chat_request(text):
        if re.search(r"\bcam\b|camera", text, re.I):
            plan.artifact = "cam"
        elif re.search(r"visuali[sz]", text, re.I):
            plan.artifact = "visualize"
        plan.intent = "chat"
        return plan

    plan.kind = "llm"
    plan.suggested_tools = []
    return plan


async def route_request_llm(message: str) -> RequestPlan | None:
    """Optional micro-router when OpenRouter is available."""
    settings = get_settings()
    if not settings.openrouter_api_key:
        return None
    try:
        from langchain_core.messages import HumanMessage, SystemMessage

        llm = get_llm("commander", temperature=0.1)
        system = """You route user messages for MARK (JARVIS assistant). Reply ONLY with JSON:
{
  "intent": "chat" | "task",
  "artifact": "none" | "briefing" | "visualize" | "cam" | "ops",
  "route": "llm" | "market_briefing" | "image_briefing" | "research_briefing",
  "subject": "short topic string",
  "symbol": "Yahoo ticker if market else empty",
  "tools": ["tool_names"]
}
Rules:
- Live stock/index/crypto price → market_briefing, market_quote
- Find/show picture/photo/image → image_briefing, image_search
- Who/what is / tell me about (not price) → research_briefing
- Build/deploy/research report as project → task, ops
- Else → llm"""
        resp = await llm.ainvoke(
            [SystemMessage(content=system), HumanMessage(content=message[:500])]
        )
        raw = (resp.content or "").strip()
        if "```" in raw:
            raw = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw, flags=re.MULTILINE).strip()
        data = json.loads(raw)
        kind = data.get("route", "llm")
        if kind not in (
            "llm",
            "market_briefing",
            "image_briefing",
            "research_briefing",
        ):
            kind = "llm"
        return RequestPlan(
            kind=kind,
            subject=str(data.get("subject") or message)[:200],
            symbol=str(data.get("symbol") or ""),
            suggested_tools=list(data.get("tools") or []),
            intent=data.get("intent", "chat"),
            artifact=data.get("artifact", "none"),
        )
    except Exception:
        return None


async def route_request(message: str, *, use_llm: bool = True) -> RequestPlan:
    """Rules first; LLM refines ambiguous short messages when enabled."""
    rules = route_request_rules(message)
    if rules.kind != "llm":
        return rules
    if not use_llm or len(message.strip()) > 220:
        return rules
    llm_plan = await route_request_llm(message)
    if llm_plan and llm_plan.kind != "llm":
        return llm_plan
    return rules
