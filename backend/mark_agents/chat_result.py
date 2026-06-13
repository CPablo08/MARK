"""Structured chat reply for API + UI artifact panel (Claude-style)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class ChatReplyResult:
    text: str
    visualize: dict[str, Any] | None = None
    briefing: dict[str, Any] | None = None
