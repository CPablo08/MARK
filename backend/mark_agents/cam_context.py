"""Cam skill context for chat replies."""

from __future__ import annotations

from mark_skills.cam import format_detections, get_latest_frame


def build_cam_context(user_id: str) -> str:
    frame = get_latest_frame(user_id)
    if not frame:
        return (
            "Cam skill: panel may be open but no frame has been uploaded yet. "
            "Ask the user to allow camera access and wait ~2 seconds."
        )
    det = format_detections(frame.get("detections", []))
    updated = frame.get("updated_at", "unknown")
    return (
        f"Cam skill: ACTIVE. Latest browser frame at {updated}.\n{det}\n"
        "When the user asks what you see, what's on camera, or similar, you MUST call "
        "cam_analyze with their exact question. Never say you cannot see or lack vision — "
        "frames are uploaded from the browser every ~2s."
    )
