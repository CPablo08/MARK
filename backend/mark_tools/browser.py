"""Web search and browsing for MARK chat (Playwright + HTTP)."""

from __future__ import annotations

import html
import re
from urllib.parse import quote_plus, urlparse

import httpx

_browser = None
_playwright = None
_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}


async def get_browser():
    global _browser, _playwright
    if _browser is None:
        try:
            from playwright.async_api import async_playwright

            _playwright = await async_playwright().start()
            _browser = await _playwright.chromium.launch(headless=True)
        except Exception:
            return None
    return _browser


async def shutdown_browser() -> None:
    global _browser, _playwright
    if _browser:
        try:
            await _browser.close()
        except Exception:
            pass
        _browser = None
    if _playwright:
        try:
            await _playwright.stop()
        except Exception:
            pass
        _playwright = None


def _clean_text(text: str, limit: int = 4000) -> str:
    text = re.sub(r"\s+", " ", html.unescape(text or "")).strip()
    return text[:limit] + ("…" if len(text) > limit else "")


async def web_search(query: str, max_results: int = 5) -> str:
    """Search the web via DuckDuckGo (no API key)."""
    q = query.strip()
    if not q:
        return "Search query was empty."
    max_results = max(1, min(max_results, 8))

    # Try HTML search first (fast)
    try:
        async with httpx.AsyncClient(
            timeout=20, headers=_HEADERS, follow_redirects=True
        ) as client:
            r = await client.post(
                "https://html.duckduckgo.com/html/",
                data={"q": q, "b": "", "kl": "us-en"},
            )
            r.raise_for_status()
            body = r.text
        results: list[tuple[str, str, str]] = []
        for block in re.finditer(
            r'class="result__a"[^>]*href="([^"]+)"[^>]*>(.*?)</a>.*?'
            r'class="result__snippet"[^>]*>(.*?)</a>',
            body,
            re.DOTALL | re.IGNORECASE,
        ):
            url = html.unescape(block.group(1))
            title = _clean_text(re.sub(r"<[^>]+>", "", block.group(2)), 200)
            snippet = _clean_text(re.sub(r"<[^>]+>", "", block.group(3)), 300)
            if url.startswith("http"):
                results.append((title, url, snippet))
            if len(results) >= max_results:
                break

        if not results:
            for m in re.finditer(
                r'class="result__a"[^>]*href="([^"]+)"[^>]*>(.*?)</a>',
                body,
                re.DOTALL | re.IGNORECASE,
            ):
                url = html.unescape(m.group(1))
                title = _clean_text(re.sub(r"<[^>]+>", "", m.group(2)), 200)
                if url.startswith("http"):
                    results.append((title, url, ""))
                if len(results) >= max_results:
                    break

        if results:
            lines = [f"Web search: “{q}” ({len(results)} results)\n"]
            for i, (title, url, snippet) in enumerate(results, 1):
                lines.append(f"{i}. **{title}**\n   {url}")
                if snippet:
                    lines.append(f"   {snippet}")
            lines.append("\nUse browse_url on a link for full page text.")
            return "\n".join(lines)
    except Exception as e:
        http_err = str(e)
    else:
        http_err = ""

    # Playwright fallback
    browser = await get_browser()
    if not browser:
        return (
            f"Web search failed ({http_err or 'no browser'}). "
            "Install Playwright: `pip install playwright && playwright install chromium`"
        )

    try:
        page = await browser.new_page()
        await page.goto(
            f"https://duckduckgo.com/?q={quote_plus(q)}&ia=web",
            timeout=25000,
            wait_until="domcontentloaded",
        )
        items = await page.evaluate(
            """() => {
              const out = [];
              document.querySelectorAll('article[data-testid="result"], .result').forEach(el => {
                const a = el.querySelector('a[href^="http"]');
                if (!a) return;
                const title = (a.innerText || '').trim();
                const href = a.href;
                const sn = el.querySelector('[data-result="snippet"], .result__snippet');
                const snippet = sn ? (sn.innerText || '').trim() : '';
                if (title && href) out.push({ title, href, snippet });
              });
              return out.slice(0, 8);
            }"""
        )
        await page.close()
        if items:
            lines = [f"Web search: “{q}”\n"]
            for i, item in enumerate(items[:max_results], 1):
                lines.append(
                    f"{i}. **{item.get('title', '')}**\n   {item.get('href', '')}\n   {item.get('snippet', '')}"
                )
            return "\n".join(lines)
    except Exception as e:
        return f"Web search failed: {e}"

    return f"No results found for “{q}”."


async def browse_url(url: str, max_chars: int = 5000) -> str:
    """Open a URL and return readable page text."""
    raw = url.strip()
    if not raw:
        return "URL was empty."
    if not raw.startswith(("http://", "https://")):
        raw = "https://" + raw

    parsed = urlparse(raw)
    if not parsed.netloc:
        return f"Invalid URL: {url}"

    browser = await get_browser()
    if not browser:
        # HTTP fallback for static pages
        try:
            async with httpx.AsyncClient(
                timeout=20, headers=_HEADERS, follow_redirects=True
            ) as client:
                r = await client.get(raw)
                r.raise_for_status()
                text = _clean_text(re.sub(r"<script[^>]*>.*?</script>", "", r.text, flags=re.I | re.S), max_chars)
                return f"URL: {raw}\n(HTTP fetch — no JavaScript)\n\n{text}"
        except Exception as e:
            return (
                f"Browser unavailable ({e}). Install: "
                "`pip install playwright && playwright install chromium`"
            )

    try:
        page = await browser.new_page()
        await page.goto(raw, timeout=30000, wait_until="domcontentloaded")
        await page.wait_for_timeout(800)
        title = await page.title()
        text = await page.evaluate(
            """() => {
              const main = document.querySelector('main, article, [role="main"]') || document.body;
              return (main.innerText || '').trim();
            }"""
        )
        await page.close()
        preview = _clean_text(text, max_chars)
        return f"**{title}**\n{raw}\n\n{preview}"
    except Exception as e:
        return f"Could not browse {raw}: {e}"


async def web_research(query: str) -> str:
    """Search the web and read the top result."""
    search = await web_search(query, max_results=3)
    url_match = re.search(r"https?://[^\s\]\)]+", search)
    if not url_match:
        return search
    top_url = url_match.group(0).rstrip(".,)")
    page = await browse_url(top_url, max_chars=3500)
    return f"{search}\n\n---\n**Top page read:**\n{page}"
