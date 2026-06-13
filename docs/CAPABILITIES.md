# What MARK can do

Full reference for chat, voice, and Operations. Ask MARK *"what can you do?"* for this list in-app.

## Conversation

- **Chat** — Questions, planning, writing, coding help, JARVIS-style voice or text.
- **Voice** — Tap mic for hands-free; MARK speaks replies (ElevenLabs Daniel voice).

## Center workspace (instant — not Operations)

- **Visualize** — Interactive HTML in the center: charts, calculators, Newton's cradle, dashboards. Say *visualize…* or *interactive calculator*.
- **Cam** — Live webcam + object detection. Say *activate camera skill*; then *what do you see?*

## Web & research (chat tools — fast)

- **web_search** — DuckDuckGo search with links.
- **web_research** — Search + read top result.
- **image_search** — Find pictures on the web (center gallery).
- **web_briefing** — Research panel with images, summary, sources, and live quotes.
- **browse_url** — Read any URL headlessly (text for MARK).
- **open_website** — Open a link in **your** browser (Safari/Chrome).
- **market_quote** — Stock/crypto/index prices (also opens a market card in Research).

## Operations (background tasks — Ops panel)

- Multi-agent pipeline: planner → research → browser → coding → verification.
- Best for: *research X*, *build me an app*, long reports, batch work.
- When done: notification + **MARK Report** — ask follow-ups in chat; MARK interprets the report using `get_task_report` and the report context you pass after opening a result.

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
- Big projects → **Operations**; then chat about the report (*"What did you find?"*, *"Summarize the report"*).
