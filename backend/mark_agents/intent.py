"""Classify user input: conversation vs autonomous task."""

import re
from typing import Literal

from mark_agents.llm import get_llm

Intent = Literal["chat", "task"]

_TASK_VERBS = re.compile(
    r"\b("
    r"build|create|implement|deploy|develop|write|code|fix|debug|refactor|"
    r"research|analyze|analyse|investigate|compare|summarize|summarise|"
    r"scrape|crawl|download|upload|organize|organise|"
    r"automate|schedule|"
    r"set up|setup|configure|install|migrate|integrate|"
    r"plan and|design and|build me|make me a|help me build"
    r")\b",
    re.I,
)

# Q&A / lookups use quick chat + tools — not the autonomous task pipeline
_TOOL_CHAT = re.compile(
    r"\b(github|gitlab|repo|repositories|account|mcp|plugin|memory|vault|"
    r"stock|stocks|price|market|s&p|nasdaq|dow|bitcoin|crypto|ticker|quote)\b",
    re.I,
)

# Built-in skills/plugins — always quick chat + native tools (never Ops task pipeline)
_SKILL_CHAT = re.compile(
    r"\b("
    r"cam skill|camera skill|open (the )?cam(?:era)?|start (the )?cam|"
    r"activate (the )?(cam|camera)(?: skill)?|use (the )?cam|turn on (the )?cam|"
    r"visualize(?: plugin)?|open (the )?visuali[sz]ation|show (me )?(a )?(chart|graph)|"
    r"income projection|savings? (calculator|projection|scenario)|interactive (calculator|chart|file|tool)|"
    r"calculator.*(savings?|rate|month|year|period)|adjust (the )?(savings|rate|amount)|"
    r"close (the )?cam|close (the )?visuali[sz]ation|visualize_close|cam_close"
    r")\b",
    re.I,
)

_VISUALIZE_CHAT = re.compile(
    r"\b("
    r"visuali[sz]e|chart|graph|dashboard|projection|scenario|interactive|calculator|"
    r"sliders?|what.?if|compound interest|save\s*\$"
    r")\b",
    re.I,
)

_ONLINE_TASK = re.compile(
    r"\b("
    r"go to|open (?:in )?(?:my |the )?browser|open (?:this )?(?:url|link|site|website)|"
    r"browse|search (?:the )?web|look up online|on (?:the )?internet|"
    r"book|order|sign up|log in|fill out|submit (?:a )?form|check (?:this )?site|"
    r"compare prices|find (?:me )?a|visit (?:this )?"
    r")\b",
    re.I,
)

_CHAT_HINTS = re.compile(
    r"^(hi|hello|hey|thanks|thank you|ok|okay|yes|no|sure|got it)[\s!.?]*$|"
    r"\b(what is|what's|who is|who's|how do i|how to|how would i|how can i|"
    r"why is|when is|where is|what do you mean|what were we|what did we|"
    r"tell me about|explain|describe|define|can you tell|do you know|"
    r"current price|stock market|s&p|give you access)\b",
    re.I,
)

_STRONG_TASK = re.compile(
    r"\b(build me|create a|implement|deploy|automate|write a full|research and write)\b",
    re.I,
)


def is_visualize_request(message: str) -> bool:
    return bool(_VISUALIZE_CHAT.search(message.strip()))


def is_online_task_request(message: str) -> bool:
    return bool(_ONLINE_TASK.search(message.strip()))


def is_skill_chat_request(message: str) -> bool:
    text = message.strip()
    if _SKILL_CHAT.search(text):
        return True
    from mark_tools.visualize_templates import (
        is_html_visualize_request,
        is_savings_calculator_request,
    )

    return is_savings_calculator_request(text) or is_html_visualize_request(text)


def is_cam_skill_request(message: str) -> bool:
    return bool(
        re.search(
            r"\b(cam skill|camera skill|open (the )?cam|start (the )?cam|"
            r"activate (the )?(cam|camera)|use (the )?cam|turn on (the )?cam)\b",
            message,
            re.I,
        )
    )


_CAM_VISION = re.compile(
    r"\b("
    r"what (are you |do you )?see(ing)?|what am i showing|what('s| is) (in |on )?(the )?cam(?:era)?|"
    r"describe (what you see|the scene|the room|what you('re| are) seeing)|"
    r"look(ing)? at (right now|now)|what can you see|tell me what you see|"
    r"camera (is )?active.*see|see(ing)? (in |on |through )?(the )?cam"
    r")\b",
    re.I,
)


def is_cam_vision_question(message: str) -> bool:
    return bool(_CAM_VISION.search(message.strip()))


def _heuristic_intent(message: str) -> Intent | None:
    text = message.strip()
    if not text:
        return "chat"
    if is_skill_chat_request(text):
        return "chat"
    if "?" in text and not _STRONG_TASK.search(text):
        return "chat"
    if len(text) < 120 and _CHAT_HINTS.search(text):
        return "chat"
    if _TOOL_CHAT.search(text) and not re.search(
        r"\b(build|create|implement|deploy|automate)\b", text, re.I
    ):
        return "chat"
    if _TASK_VERBS.search(text):
        if is_visualize_request(text) or is_skill_chat_request(text) or is_online_task_request(text):
            return "chat"
        return "task"
    if len(text) > 180 and (
        text.count(".") >= 2
        or " and then " in text.lower()
        or " step " in text.lower()
        or text.count("\n") >= 2
    ):
        return "task"
    if text.endswith("?") and len(text) < 160 and not _TASK_VERBS.search(text):
        return "chat"
    return None


async def classify_intent(message: str) -> Intent:
    """Decide if MARK should converse or run the full task pipeline."""
    hint = _heuristic_intent(message)
    if hint:
        return hint

    try:
        llm = get_llm("commander", temperature=0.1)
        prompt = f"""You route requests for MARK, a personal AI assistant.

Reply with exactly one word: CHAT or TASK.

CHAT = questions, memory, GitHub, web browse/search, most "do X online" requests, Cam/Visualize in center panel.
TASK = large multi-step software projects or long autonomous research — NOT quick web lookups or interactive HTML calculators.

User message:
{message[:800]}"""
        result = await llm.ainvoke(prompt)
        raw = (result.content if hasattr(result, "content") else str(result)).strip().upper()
        if "TASK" in raw:
            return "task"
        return "chat"
    except Exception:
        return "task" if len(message) > 120 and _TASK_VERBS.search(message) else "chat"


async def generate_task_ack(objective: str, *, for_voice: bool = True) -> str:
    """Short acknowledgment before autonomous execution."""
    if for_voice:
        return (
            "Very good — I'll see to that now. "
            "You can follow progress in Operations."
        )
    return (
        "**Task started.** I'm working on that in the background. "
        "Open **Operations** to follow progress."
    )
