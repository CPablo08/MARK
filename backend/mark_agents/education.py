"""Academic integrity — narrow blocks only for explicit cheating, not general online work."""

from __future__ import annotations

import re

_SCHOOL_PLATFORM = re.compile(
    r"\b(khan academy|canvas|blackboard|schoology|moodle|google classroom)\b",
    re.I,
)
_EXPLICIT_CHEAT = re.compile(
    r"\b("
    r"auto[- ]?complete (?:the |my )?(?:course|skills?|homework|assignment)|"
    r"do my homework|submit (?:the )?answers for me|cheat on|fake my (?:work|grade)|"
    r"farm mastery|100% (?:for me|without)|complete (?:all )?skills? for me"
    r")\b",
    re.I,
)
_CAPABILITY_QUESTION = re.compile(
    r"\b("
    r"can you|are you able|do you support|virtually any|any task online|"
    r"what can you do|like khan academy\b.*\b(example|mean)|"
    r"online tasks?|browse the web|do stuff online"
    r")\b",
    re.I,
)


def is_academic_cheat_request(message: str) -> bool:
    """True only for explicit 'do my graded work for me' — not general online capability."""
    text = message.strip()
    if not text or _CAPABILITY_QUESTION.search(text):
        return False
    return bool(_SCHOOL_PLATFORM.search(text) and _EXPLICIT_CHEAT.search(text))


def academic_integrity_reply(*, for_voice: bool = False) -> str:
    if for_voice:
        return (
            "I won't auto-submit graded schoolwork for you — that's cheating and against platform rules. "
            "I can still tutor you, walk through problems, or handle most other tasks on the web. "
            "What are we working on?"
        )
    return (
        "I won't **auto-complete graded assignments** on your behalf (Khan Academy, Canvas, etc.) — "
        "that's academic dishonesty and violates platform terms.\n\n"
        "I **can** still help online: research, browsing, explanations, practice problems, "
        "and virtually any other legitimate web task. Tell me what you need."
    )
