"""Cam skill — camera frames + detection cache for agent tools."""

from __future__ import annotations

import base64
import re
from datetime import datetime, timezone
from typing import Any

from mark_core.events import publish_ws

# user_id -> latest frame payload
_frame_cache: dict[str, dict[str, Any]] = {}


async def open_cam_skill(user_id: str, objective: str = "Observe the scene") -> None:
    await publish_ws(
        user_id,
        "skill.cam.open",
        {"objective": objective.strip() or "Observe the scene"},
    )


async def close_cam_skill(user_id: str) -> None:
    _frame_cache.pop(user_id, None)
    await publish_ws(user_id, "skill.cam.close", {})


def store_frame(
    user_id: str,
    *,
    image_base64: str,
    detections: list[dict[str, Any]] | None = None,
    width: int = 0,
    height: int = 0,
) -> None:
    _frame_cache[user_id] = {
        "image_base64": image_base64,
        "detections": detections or [],
        "width": width,
        "height": height,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }


def get_latest_frame(user_id: str) -> dict[str, Any] | None:
    return _frame_cache.get(user_id)


def format_detections(detections: list[dict[str, Any]]) -> str:
    if not detections:
        return "No objects detected in the latest frame."
    lines = []
    for d in detections[:20]:
        label = d.get("class", d.get("label", "object"))
        score = d.get("score", d.get("confidence", 0))
        if isinstance(score, float):
            lines.append(f"- {label} ({score:.0%})")
        else:
            lines.append(f"- {label}")
    return "Detections:\n" + "\n".join(lines)


async def analyze_latest_frame(user_id: str, question: str) -> str:
    """Describe latest camera frame using vision model + local detections."""
    frame = get_latest_frame(user_id)
    if not frame:
        return (
            "No camera frame available yet. The Cam skill may still be starting, "
            "or the user has not granted camera permission."
        )

    det_text = format_detections(frame.get("detections", []))
    image_b64 = frame.get("image_base64", "")
    if not image_b64:
        return det_text

    try:
        from mark_agents.llm import get_llm
        from langchain_core.messages import HumanMessage

        # Vision-capable model on OpenRouter
        llm = get_llm("commander", temperature=0.2)
        if "gpt-4o" not in str(getattr(llm, "model_name", "")):
            llm.model_name = "openai/gpt-4o-mini"

        data_url = image_b64
        if not data_url.startswith("data:"):
            data_url = f"data:image/jpeg;base64,{image_b64}"

        msg = HumanMessage(
            content=[
                {
                    "type": "text",
                    "text": (
                        f"{question}\n\nLocal CV detections:\n{det_text}\n"
                        "Describe what you see in the image concisely."
                    ),
                },
                {"type": "image_url", "image_url": {"url": data_url}},
            ]
        )
        result = await llm.ainvoke([msg])
        text = result.content if hasattr(result, "content") else str(result)
        return f"{text.strip()}\n\n---\n{det_text}"
    except Exception as e:
        return f"{det_text}\n\n(Vision model unavailable: {e})"
