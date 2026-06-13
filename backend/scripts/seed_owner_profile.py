#!/usr/bin/env python3
"""One-shot: seed vault with owner profile, credentials (references only), and plugins."""

import asyncio

from mark_core.db import SessionLocal
from mark_core.auth import get_or_create_local_user
from mark_memory.service import store_memory


ENTRIES: list[tuple[str, str, str]] = [
    # --- Owner / semantic ---
    (
        "semantic",
        "Owner profile",
        """MARK personal install — single local user (personal_mode).
Primary developer context: CPablo08 on GitHub (5 public repos).
Workspace: /Users/conradpablo/Desktop/Mark (monorepo).
UI preferences: dark steel-blue accent, JARVIS-like masculine voice (ElevenLabs Daniel),
auto chat vs task intent (no manual mode toggle), ChatGPT-style tap-to-talk voice sessions,
separate chat threads per voice session / New chat.""",
    ),
    (
        "semantic",
        "MARK product definition",
        """MARK = Machine Augmented Reasoning and Knowledgebase.
Local-first assistant: chat, voice, memory vault graph, plugins (MCP), ops/tasks, vault credentials.
Stack: FastAPI backend, React UI (Vite), optional Tauri desktop, SQLite, Redis optional, Qdrant optional.
Run: make api (port 8000), pnpm dev (port 5173). Default LLM: openai/gpt-4o-mini via OpenRouter.""",
    ),
    # --- Project ---
    (
        "project",
        "MARK repository",
        """Monorepo layout: backend/mark_*, packages/ui, packages/shared, apps/desktop.
Key env file: .env at repo root (also backend/.env). Frontend: apps/desktop/.env with VITE_API_URL.
Auth: personal mode — GET /auth/session, owner@local, no login UI.""",
    ),
    # --- Credentials (references only — never store secret values) ---
    (
        "credential",
        "OpenRouter",
        "Variable: OPENROUTER_API_KEY\nLocation: .env (repo root)\nStatus: configured\nModel default: openai/gpt-4o-mini\nNote: secret value stored only in .env, not in vault.",
    ),
    (
        "credential",
        "ElevenLabs TTS",
        "Variable: ELEVENLABS_API_KEY\nLocation: .env\nStatus: configured\nVoice: Daniel (onwK4e9ZLuTAKqWW03F9), model eleven_turbo_v2_5\nNote: secret value stored only in .env.",
    ),
    (
        "credential",
        "GitHub — MARK backend",
        "Variable: GITHUB_TOKEN\nLocation: .env\nStatus: not set in .env (optional for github_list_repos / github_account tools)\nUse: add PAT to .env for in-app GitHub tools.",
    ),
    (
        "credential",
        "GitHub — Cursor / dev machine",
        "Tool: gh CLI\nAccount: CPablo08\nStatus: logged in (keyring)\nScopes: gist, read:org, repo, workflow\nNote: used by Cursor agent shell, separate from MARK GITHUB_TOKEN.",
    ),
    (
        "credential",
        "OpenAI / Whisper",
        "Variable: OPENAI_API_KEY\nLocation: .env\nStatus: not set\nWHISPER_BACKEND: local (base model)\nNote: set OPENAI_API_KEY + WHISPER_BACKEND=openai for cloud STT.",
    ),
    (
        "credential",
        "JWT (local)",
        "Variable: JWT_SECRET\nLocation: .env\nStatus: dev placeholder (change for production)",
    ),
    (
        "credential",
        "Vercel",
        "Location: Cursor Vercel plugin/MCP (not in MARK .env)\nStatus: plugin installed in Cursor; authenticate via Cursor Integrations\nNote: MARK app does not embed Vercel API keys.",
    ),
    # --- Plugins / procedural ---
    (
        "procedural",
        "MARK MCP plugins (registered)",
        """Enabled integrations in MARK:
1. GitHub MCP — npx @modelcontextprotocol/server-github (stdio; bridge stub — prefer built-in github_* tools + GITHUB_TOKEN)
2. Filesystem MCP — npx @modelcontextprotocol/server-filesystem
3. Browser MCP — npx @anthropic/mcp-browser

Manage via UI: Plugins panel (/integrations).""",
    ),
    (
        "procedural",
        "Cursor MCP (IDE, not MARK DB)",
        """Cursor-enabled MCP servers for this workspace:
- cursor-ide-browser (page test/automation)
- plugin-vercel-vercel (deploy/env; sign in via Cursor)

These are IDE tools, not synced into MARK integrations unless added manually.""",
    ),
    (
        "agent",
        "MARK chat tools",
        """Built-in chat tools: github_account, github_list_repos, memory_search.
Intent routing: chat (Q&A + tools) vs task (autonomous ops pipeline).
GitHub/repo questions should use chat path, not task path.""",
    ),
    # --- Episodic ---
    (
        "episodic",
        "Setup session summary (2026-05)",
        """Built personal MARK UI: bottom bar, particle orb, vault memory graph, voice I/O.
Fixed: OpenRouter model, duplicate messages, auto intent, ElevenLabs JARVIS voice, HTTP chat replies,
separate chats (new_chat / voice session), vault collapsible panels.
Outstanding: ensure TTS playback after browser unlock; add GITHUB_TOKEN to .env for in-app GitHub.""",
    ),
]


async def main() -> None:
    async with SessionLocal() as db:
        user = await get_or_create_local_user(db)
        user_id = user.id
        created = 0
        for category, label, content in ENTRIES:
            await store_memory(
                db,
                user_id,
                category,
                content,
                scope="vault",
                metadata={"label": label, "source": "cursor_seed"},
            )
            created += 1
        await db.commit()
        print(f"Seeded {created} vault memories for user {user_id}")


if __name__ == "__main__":
    asyncio.run(main())
