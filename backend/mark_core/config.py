from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# Repo root: Mark/
ROOT_DIR = Path(__file__).resolve().parents[2]
_ENV_FILES = (
    ROOT_DIR / ".env",
    ROOT_DIR / "backend" / ".env",
    Path(".env"),
)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=[str(p) for p in _ENV_FILES if p.exists()] or ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str = "sqlite+aiosqlite:///./backend/mark.db"
    redis_url: str = "redis://localhost:6379/0"
    qdrant_url: str = "http://localhost:6333"
    openrouter_api_key: str = ""
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    openrouter_default_model: str = "openai/gpt-4o-mini"
    github_token: str = ""
    openai_api_key: str = ""
    openai_base_url: str = "https://api.openai.com/v1"
    elevenlabs_api_key: str = ""
    # ElevenLabs "Daniel" — British male JARVIS-style (override in .env)
    elevenlabs_voice_id: str = "onwK4e9ZLuTAKqWW03F9"
    elevenlabs_model_id: str = "eleven_turbo_v2_5"
    elevenlabs_stability: float = 0.58
    elevenlabs_similarity_boost: float = 0.75
    elevenlabs_style: float = 0.42
    elevenlabs_speed: float = 1.12
    personal_mode: bool = True
    local_owner_email: str = "owner@local"
    jwt_secret: str = "change-me"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    refresh_token_expire_days: int = 7
    whisper_backend: str = "local"
    whisper_model: str = "base"
    safety_default_mode: str = "assisted"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    cors_origins: str = "http://localhost:5173,tauri://localhost,http://127.0.0.1:5173"
    embedding_model: str = "openai/text-embedding-3-small"
    embedding_dim: int = 1536
    sandbox_dir: str = str(ROOT_DIR / "sandbox")
    # Supervised terminal: only allow cwd inside sandbox unless True
    terminal_allow_outside_sandbox: bool = False
    # SMTP (supervised email — MARK sends only after in-app approval)
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_tls: bool = True
    smtp_username: str = ""
    smtp_password: str = ""
    smtp_from_email: str = ""
    # Twilio (optional): SMS + outbound voice after approval
    twilio_account_sid: str = ""
    twilio_auth_token: str = ""
    twilio_from_number: str = ""
    twilio_voice_twiml_url: str = ""
    # Open http(s) links in the user's default browser (Safari, Chrome, …)
    browser_open_enabled: bool = True


def _normalize_database_url(url: str) -> str:
    if not url.startswith("sqlite"):
        return url
    if ":///" not in url:
        return url
    path_part = url.split("///", 1)[1]
    if path_part.startswith("/") and not path_part.startswith("//"):
        # already absolute (unix)
        db_path = Path(path_part)
    else:
        # relative — resolve from repo root
        db_path = (ROOT_DIR / path_part.lstrip("./")).resolve()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    return f"sqlite+aiosqlite:///{db_path}"


@lru_cache
def get_settings() -> Settings:
    s = Settings()
    normalized = _normalize_database_url(s.database_url)
    sandbox = str((ROOT_DIR / "sandbox").resolve())
    s = s.model_copy(update={"database_url": normalized, "sandbox_dir": sandbox})
    Path(s.sandbox_dir).mkdir(parents=True, exist_ok=True)
    return s
