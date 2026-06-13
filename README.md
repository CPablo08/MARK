# MARK

**Machine Augmented Reasoning and Knowledgebase** — a cloud-native autonomous executive AI system.

## Quick start

### One command (recommended)

```bash
cp .env.example .env
# Add OPENROUTER_API_KEY and ELEVENLABS_API_KEY to .env
make install
make start      # API + worker + UI — opens browser
```

Stop everything: `make stop` or `./scripts/stop.sh`

Logs: `tail -f .mark/logs/api.log .mark/logs/ui.log`

Options: `./scripts/start.sh --docker` (postgres/redis/qdrant), `--no-worker`, `--open`

### Manual (separate terminals)

```bash
make env-sync
make api        # http://127.0.0.1:8000
make worker     # optional; tasks also run inline without Redis
make ui         # http://localhost:5173
```

### 4. Tauri desktop (requires Rust)

```bash
rustup install stable
pnpm --filter @mark/desktop tauri dev
```

## Docker (production)

```bash
# Set DATABASE_URL=postgresql+asyncpg://mark:mark@postgres:5432/mark in .env
make docker-up
docker compose -f docker/docker-compose.yml up --build api worker
```

## Architecture

| Layer | Stack |
|-------|-------|
| UI | React 19, Tailwind 4, Framer Motion, Three.js orb |
| Desktop | Tauri 2 |
| API | FastAPI, WebSockets, JWT |
| Agents | Commander + Planner, Research, Browser, Coding, Verification, Memory |
| Data | SQLite (dev) / PostgreSQL, Redis, Qdrant |
| Models | OpenRouter |
| Voice | Whisper STT, ElevenLabs TTS |

## Key paths

- `.env` — API keys and config (never commit)
- `apps/desktop/.env` — `VITE_API_URL=http://127.0.0.1:8000`
- `backend/mark.db` — SQLite database (dev)

## Troubleshooting

| Issue | Fix |
|-------|-----|
| WebSocket not streaming | Restart API; works without Redis via in-process bus |
| Database error | Run `make env-sync`; DB path resolves to `backend/mark.db` |
| LLM errors | Verify `OPENROUTER_API_KEY` in `.env` |
| Tauri won't build | Install Rust: `curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs \| sh` |

## License

Proprietary — MARK © 2026
