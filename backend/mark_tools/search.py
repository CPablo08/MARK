import httpx


async def web_search(query: str) -> str:
    """Lightweight search via DuckDuckGo instant answer API."""
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(
                "https://api.duckduckgo.com/",
                params={"q": query, "format": "json", "no_html": 1},
            )
            data = resp.json()
            abstract = data.get("AbstractText", "")
            related = data.get("RelatedTopics", [])[:3]
            snippets = [t.get("Text", "") for t in related if isinstance(t, dict)]
            return abstract or "\n".join(snippets) or f"No instant results for: {query}"
    except Exception as e:
        return f"Search unavailable: {e}. Query: {query}"
