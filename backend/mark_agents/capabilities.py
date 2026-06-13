"""What MARK can do — for users and system prompts."""

from __future__ import annotations

import re

_CAPABILITIES_Q = re.compile(
    r"\b("
    r"what can you do|what are you capable|list (?:your )?capabilities|"
    r"what do you support|how can you help|what are your features|"
    r"everything you can do|full list|help me understand what mark"
    r")\b",
    re.I,
)

# Condensed for every chat turn (token-efficient)
CAPABILITIES_SYSTEM = """MARK capability summary (use tools — do not claim you cannot):
• Chat: JARVIS-style assistant; voice or text; remembers vault notes.
• Operations: multi-step tasks (research, code, browser) — progress in Ops; ask about reports via chat.
• Visualize: interactive HTML/charts/calculators in center panel (visualize tool).
• Cam: live camera + object detection in center (cam / cam_analyze).
• Web: web_search, web_research, image_search, web_briefing (gallery + sources in Research panel), browse_url, open_website.
• Markets: market_quote for tickers.
• GitHub: account + repos (GITHUB_TOKEN).
• Memory: memory_search / memory_remember (vault).
• Supervised (approval dialog): terminal commands, email (SMTP), SMS/call (Twilio), travel search.
• Plugins: MCP tools from Plugins panel.
• Not allowed: auto-submit graded schoolwork; destructive shell."""

MARK_CAPABILITIES_FULL = """# What MARK can do

## Conversation
- **Chat** — Questions, planning, writing, coding help, JARVIS-style voice or text.
- **Voice** — Tap mic for hands-free; MARK speaks replies (ElevenLabs Daniel voice).

## Center workspace (instant — not Operations)
- **Visualize** — Interactive HTML in the center: charts, calculators, Newton's cradle, dashboards. Say *visualize…* or *interactive calculator*.
- **Cam** — Live webcam + object detection. Say *activate camera skill*; then *what do you see?*

## Web & research (chat tools — fast)
- **web_search** — DuckDuckGo search with links.
- **web_research** — Search + read top result.
- **web_briefing** — *Who is X?* / *What is Y?* — center Research panel with image, summary, cited sources.
- **browse_url** — Read any URL headlessly (text for MARK).
- **open_website** — Open a link in **your** browser (Safari/Chrome).
- **market_quote** — Stock/crypto/index prices.

## Operations (background tasks — Ops panel)
- Multi-agent pipeline: planner → research → browser → coding → verification.
- Best for: *research X*, *build me an app*, long reports, batch work.
- When done: notification + **MARK Report** — ask follow-ups in chat; MARK interprets the report.

## Memory vault
- **memory_remember** / **memory_search** — Save and recall facts, preferences, notes.

## GitHub
- **github_account** / **github_list_repos** — If `GITHUB_TOKEN` is set.

## Supervised actions (you tap **Approve**)
- **run_terminal_command** — Shell in project sandbox.
- **send_email** — SMTP.
- **send_sms** / **place_phone_call** — Twilio.
- **travel_booking_assist** — Flight search (you book on airline site).

## Plugins
- Install MCP servers (Playwright, etc.) in **Plugins** — extra tools appear as `server__tool`.

## Tips for speed
- Lookups & tools → **chat** (seconds).
- Interactive UI → **visualize** / **cam** (not Ops).
- Big projects → **Operations**; then chat about the report.
"""


def is_capabilities_question(message: str) -> bool:
    return bool(_CAPABILITIES_Q.search(message.strip()))


def capabilities_reply(*, for_voice: bool = False) -> str:
    if for_voice:
        return (
            "I'm MARK — your JARVIS-style chief of staff. I search and open the web, "
            "run Operations for big projects, show interactive visuals and camera in the center, "
            "remember things in your vault, and with your approval send email, texts, or shell commands. "
            "Ask me to list capabilities in chat for the full breakdown."
        )
    return MARK_CAPABILITIES_FULL
