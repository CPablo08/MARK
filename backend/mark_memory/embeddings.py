import hashlib

from openai import AsyncOpenAI

from mark_core.config import get_settings

settings = get_settings()


async def embed_text(text: str) -> list[float]:
    if not settings.openrouter_api_key:
        return _hash_embedding(text, settings.embedding_dim)

    client = AsyncOpenAI(
        api_key=settings.openrouter_api_key,
        base_url=settings.openrouter_base_url,
    )
    try:
        resp = await client.embeddings.create(
            model=settings.embedding_model,
            input=text[:8000],
        )
        vec = resp.data[0].embedding
        if len(vec) != settings.embedding_dim:
            return _hash_embedding(text, settings.embedding_dim)
        return vec
    except Exception:
        return _hash_embedding(text, settings.embedding_dim)


def _hash_embedding(text: str, dim: int) -> list[float]:
    h = hashlib.sha256(text.encode()).digest()
    return [((h[i % len(h)] / 255.0) * 2 - 1) for i in range(dim)]
