"""Open URLs in the user's default system browser (Safari, Chrome, etc.)."""

from __future__ import annotations

import asyncio
import re
import webbrowser
from urllib.parse import urlparse

_BLOCKED_SCHEMES = frozenset({"javascript", "file", "data", "vbscript"})
_BLOCKED_HOSTS = re.compile(
    r"^(?:localhost|127\.0\.0\.1|0\.0\.0\.0|\[::1\])(?::\d+)?$",
    re.I,
)


def _normalize_url(url: str) -> str | None:
    raw = url.strip().strip("<>\"'")
    if not raw:
        return None
    if not re.match(r"^https?://", raw, re.I):
        raw = f"https://{raw}"
    parsed = urlparse(raw)
    if parsed.scheme.lower() not in ("http", "https"):
        return None
    if not parsed.netloc:
        return None
    if parsed.scheme.lower() in _BLOCKED_SCHEMES:
        return None
    return raw


def _open_sync(url: str) -> bool:
    try:
        return webbrowser.open(url, new=2)
    except Exception:
        return False


async def open_in_user_browser(url: str, *, allow_localhost: bool = False) -> str:
    """Open http(s) URL in the OS default browser. Returns status message for the agent."""
    from mark_core.config import get_settings

    settings = get_settings()
    if not getattr(settings, "browser_open_enabled", True):
        return "Opening websites in your browser is disabled in settings."

    normalized = _normalize_url(url)
    if not normalized:
        return "Invalid URL — only http:// and https:// links can be opened."

    host = urlparse(normalized).netloc.split("@")[-1]
    if not allow_localhost and _BLOCKED_HOSTS.match(host.split(":")[0]):
        return (
            f"Won't open local URL {normalized} in your browser automatically. "
            "Paste it in the address bar if you need it."
        )

    ok = await asyncio.to_thread(_open_sync, normalized)
    if ok:
        return f"Opened in your default browser: {normalized}"
    # macOS `open` fallback when webbrowser registry fails (e.g. minimal env)
    if await asyncio.to_thread(_open_via_os, normalized):
        return f"Opened in your default browser: {normalized}"
    return (
        f"Could not open {normalized} automatically. "
        "Copy the link into your browser, or check that a default browser is set."
    )


def _open_via_os(url: str) -> bool:
    import platform
    import subprocess

    system = platform.system()
    try:
        if system == "Darwin":
            subprocess.run(["open", url], check=False, timeout=8)
            return True
        if system == "Windows":
            subprocess.run(["cmd", "/c", "start", "", url], check=False, timeout=8)
            return True
        subprocess.run(["xdg-open", url], check=False, timeout=8)
        return True
    except Exception:
        return False
