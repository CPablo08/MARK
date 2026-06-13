"""Detect and answer questions about Operations / task reports."""

from __future__ import annotations

import re

_REPORT_QUESTION = re.compile(
    r"\b("
    r"report|operation(?:s)?\s+report|ops\s+report|task\s+report|mark\s+report|"
    r"what did (?:you|mark) find|what were the (?:results?|findings)|"
    r"summarize (?:the )?(?:report|results?|task)|based on (?:the )?report|"
    r"from the (?:report|task|operation)|explain (?:the )?results?|"
    r"interpret (?:the )?|according to (?:the )?report|"
    r"answer (?:my )?question.*report|backed by (?:the )?report"
    r")\b",
    re.I,
)


def is_task_report_question(message: str) -> bool:
    return bool(_REPORT_QUESTION.search(message.strip()))
