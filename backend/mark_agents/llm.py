import re

from langchain_openai import ChatOpenAI

from mark_core.config import get_settings

settings = get_settings()

# Valid OpenRouter model IDs (override via OPENROUTER_DEFAULT_MODEL in .env)
AGENT_MODELS: dict[str, str] = {
    "commander": "openai/gpt-4o-mini",
    "planner": "openai/gpt-4o-mini",
    "research": "openai/gpt-4o-mini",
    "coding": "openai/gpt-4o-mini",
    "browser": "openai/gpt-4o-mini",
    "verification": "openai/gpt-4o-mini",
    "memory": "openai/gpt-4o-mini",
    "finance": "openai/gpt-4o-mini",
}


def get_llm(role: str = "commander", temperature: float = 0.3) -> ChatOpenAI:
    if not settings.openrouter_api_key:
        raise ValueError("OPENROUTER_API_KEY is not set in .env")

    default = settings.openrouter_default_model or AGENT_MODELS["commander"]
    model = AGENT_MODELS.get(role, default)
    if role == "commander":
        model = default

    return ChatOpenAI(
        model=model,
        temperature=temperature,
        api_key=settings.openrouter_api_key,
        base_url=settings.openrouter_base_url,
        default_headers={
            "HTTP-Referer": "https://github.com/mark-ai",
            "X-Title": "MARK",
        },
    )


def format_openrouter_error(exc: Exception) -> str:
    raw = str(exc)
    if "402" in raw or "credits" in raw.lower():
        return (
            "OpenRouter needs credits for this model. Add credits at openrouter.ai "
            "or set OPENROUTER_DEFAULT_MODEL=openai/gpt-4o-mini in your .env."
        )
    if "404" in raw or "No endpoints found" in raw:
        return (
            f"Model not available on OpenRouter. Set OPENROUTER_DEFAULT_MODEL in .env "
            f"(current default: {settings.openrouter_default_model})."
        )
    if "401" in raw or "Unauthorized" in raw:
        return "OpenRouter rejected the API key. Check OPENROUTER_API_KEY in .env."
    detail = raw
    m = re.search(r"'message':\s*'([^']+)'", raw)
    if m:
        detail = m.group(1)
    return f"OpenRouter error: {detail[:280]}"
