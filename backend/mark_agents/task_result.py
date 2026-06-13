"""Classify task output for UI notifications."""
import re

_RESULT_KINDS = ("research", "search", "image", "link", "code", "report", "error")


def infer_result_kind(content: str, *, research_mode: bool = False) -> str:
    text = content or ""
    lower = text.lower()
    if re.search(
        r"!\[[^\]]*\]\([^)]+\)|https?://[^\s\)]+\.(?:png|jpe?g|webp|gif)(?:\?[^\s\)]*)?",
        text,
        re.I,
    ):
        return "image"
    urls = re.findall(r"https?://[^\s\)\]>]+", text)
    if urls and research_mode:
        return "search"
    if urls:
        return "link"
    if research_mode or "mark research" in lower:
        return "research"
    if re.search(r"```|\.py\b|\.tsx\b|repository|pull request", lower):
        return "code"
    return "report"


def preview_text(content: str, limit: int = 140) -> str:
    plain = re.sub(r"[#*_`>\[\]]", "", content or "")
    plain = re.sub(r"\s+", " ", plain).strip()
    if len(plain) <= limit:
        return plain
    return plain[: limit - 1].rstrip() + "…"
