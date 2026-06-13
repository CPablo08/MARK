"""Structured web briefings — images, summary, cited sources for the center panel."""

from __future__ import annotations

import re
import uuid
from typing import Any
from urllib.parse import quote_plus

import httpx

from mark_core.events import publish_ws
from mark_tools.browser import _HEADERS, web_search
from mark_tools.image_search import image_search
from mark_tools.market import get_market_quote, get_market_quote_data

_MARKET_EXCLUDE = re.compile(
    r"\b(stock|current price|price of|ticker|s&p|nasdaq|bitcoin|btc)\b", re.I
)

_WHO_WHAT = re.compile(
    r"^\s*(?:who|what)\s+(?:is|was|are)\s+(.+?)\??\s*$",
    re.I,
)
_TELL_ABOUT = re.compile(r"^\s*tell\s+me\s+about\s+(.+?)\??\s*$", re.I)
_IMAGE = re.compile(
    r"\b("
    r"find(?:\s+me)?\s+(?:a\s+)?(?:picture|photo|image)s?\s+(?:of|for)|"
    r"show\s+me\s+(?:a\s+)?(?:picture|photo|image)s?\s+(?:of|for)|"
    r"(?:picture|photo|image)s?\s+of|"
    r"what\s+does\s+.+\s+look\s+like"
    r")\b",
    re.I,
)


def is_image_briefing_request(message: str) -> bool:
    return bool(_IMAGE.search(message.strip()))


def is_research_briefing_request(message: str) -> bool:
    text = message.strip()
    if not text or len(text) > 220:
        return False
    if _MARKET_EXCLUDE.search(text) or is_image_briefing_request(text):
        return False
    if _WHO_WHAT.match(text) or _TELL_ABOUT.match(text):
        return True
    return bool(
        re.search(
            r"^\s*(?:search|look up|find (?:info|information) (?:on|about))\s+(.+)",
            text,
            re.I,
        )
    )


def is_web_briefing_request(message: str) -> bool:
    return is_research_briefing_request(message) or is_image_briefing_request(message)


def extract_briefing_subject(message: str) -> str:
    text = message.strip()
    m = _IMAGE.search(text)
    if m:
        for pat in (
            r"(?:picture|photo|image)s?\s+of\s+(.+?)(?:\?|$)",
            r"find(?:\s+me)?\s+(?:a\s+)?(?:picture|photo|image)s?\s+(?:of|for)\s+(.+?)(?:\?|$)",
            r"show\s+me\s+(?:a\s+)?(?:picture|photo|image)s?\s+(?:of|for)\s+(.+?)(?:\?|$)",
        ):
            sub = re.search(pat, text, re.I)
            if sub:
                return sub.group(1).strip().rstrip("?.")
    for pat in (_WHO_WHAT, _TELL_ABOUT):
        m = pat.match(text)
        if m:
            return m.group(1).strip().rstrip("?.")
    m = re.search(
        r"^\s*(?:search|look up|find (?:info|information) (?:on|about))\s+(.+?)\??\s*$",
        text,
        re.I,
    )
    if m:
        return m.group(1).strip().rstrip("?.")
    return text


def _briefing_shell(
    *,
    query: str,
    title: str,
    summary: str,
    kind: str,
    image_url: str | None = None,
    image_source: str | None = None,
    images: list[dict[str, Any]] | None = None,
    sources: list[dict[str, str]] | None = None,
    facts: list[str] | None = None,
    market: dict[str, Any] | None = None,
) -> dict[str, Any]:
    imgs = images or []
    hero = image_url or (imgs[0].get("url") if imgs else None)
    return {
        "id": str(uuid.uuid4()),
        "query": query,
        "title": title,
        "summary": summary,
        "kind": kind,
        "image_url": hero,
        "image_source": image_source or (imgs[0].get("title") if imgs else None),
        "images": imgs,
        "facts": facts or [],
        "sources": sources or [],
        "market": market,
    }


async def _ddg_instant(query: str) -> dict[str, Any]:
    out: dict[str, Any] = {}
    try:
        async with httpx.AsyncClient(timeout=12, headers=_HEADERS) as client:
            r = await client.get(
                "https://api.duckduckgo.com/",
                params={
                    "q": query,
                    "format": "json",
                    "no_html": "1",
                    "skip_disambig": "1",
                },
            )
            r.raise_for_status()
            data = r.json()
        abstract = (data.get("AbstractText") or "").strip()
        if abstract:
            out["summary"] = abstract
        heading = (data.get("Heading") or "").strip()
        if heading:
            out["title"] = heading
        img = (data.get("Image") or "").strip()
        if img:
            if img.startswith("//"):
                img = "https:" + img
            out["image_url"] = img
            out["image_source"] = (data.get("AbstractSource") or "DuckDuckGo").strip()
        url = (data.get("AbstractURL") or "").strip()
        if url:
            out["primary_source"] = {
                "title": data.get("AbstractSource") or heading or query,
                "url": url,
                "snippet": abstract[:280] if abstract else "",
            }
    except Exception:
        pass
    return out


async def _wikipedia_summary(subject: str) -> dict[str, Any]:
    title = subject.replace(" ", "_")
    for attempt in (title, title.title()):
        try:
            async with httpx.AsyncClient(timeout=12, headers=_HEADERS) as client:
                r = await client.get(
                    f"https://en.wikipedia.org/api/rest_v1/page/summary/{quote_plus(attempt)}",
                )
                if r.status_code == 404:
                    continue
                r.raise_for_status()
                data = r.json()
            extract = (data.get("extract") or "").strip()
            page_url = (data.get("content_urls") or {}).get("desktop", {}).get("page", "")
            thumb = (data.get("thumbnail") or {}).get("source", "")
            return {
                "title": data.get("title") or subject,
                "summary": extract,
                "image_url": thumb or None,
                "image_source": "Wikipedia",
                "primary_source": {
                    "title": f"Wikipedia — {data.get('title') or subject}",
                    "url": page_url,
                    "snippet": extract[:280] if extract else "",
                },
            }
        except Exception:
            continue
    return {}


def _parse_search_sources(search_text: str, limit: int = 6) -> list[dict[str, str]]:
    sources: list[dict[str, str]] = []
    for block in re.finditer(
        r"\d+\.\s+\*\*(.+?)\*\*\s*\n\s+(https?://\S+)(?:\s*\n\s+(.+))?",
        search_text,
        re.MULTILINE,
    ):
        sources.append(
            {
                "title": block.group(1).strip(),
                "url": block.group(2).strip(),
                "snippet": (block.group(3) or "").strip()[:300],
            }
        )
        if len(sources) >= limit:
            break
    return sources


async def build_web_briefing(query: str) -> dict[str, Any]:
    """Aggregate instant answers, Wikipedia, and web search into a briefing payload."""
    subject = extract_briefing_subject(query)
    ddg = await _ddg_instant(subject)
    wiki = await _wikipedia_summary(subject)
    search_raw = await web_search(subject, max_results=6)
    search_sources = _parse_search_sources(search_raw)

    title = wiki.get("title") or ddg.get("title") or subject
    summary = wiki.get("summary") or ddg.get("summary") or ""
    if not summary and search_sources:
        summary = search_sources[0].get("snippet", "")

    image_url = wiki.get("image_url") or ddg.get("image_url")
    image_source = wiki.get("image_source") or ddg.get("image_source")

    sources: list[dict[str, str]] = []
    seen_urls: set[str] = set()

    def add_source(s: dict[str, str]) -> None:
        url = (s.get("url") or "").strip()
        if not url or url in seen_urls:
            return
        seen_urls.add(url)
        sources.append(
            {
                "title": (s.get("title") or url)[:200],
                "url": url,
                "snippet": (s.get("snippet") or "")[:400],
            }
        )

    primary = wiki.get("primary_source") or ddg.get("primary_source")
    if primary:
        add_source(primary)
    for s in search_sources:
        add_source(s)

    facts: list[str] = []
    if summary:
        for sent in re.split(r"(?<=[.!?])\s+", summary):
            s = sent.strip()
            if 40 < len(s) < 220:
                facts.append(s)
            if len(facts) >= 4:
                break

    return _briefing_shell(
        query=subject,
        title=title,
        summary=summary or f"No summary found for “{subject}”. See sources below.",
        kind="research",
        image_url=image_url,
        image_source=image_source,
        sources=sources[:8],
        facts=facts,
    )


async def build_image_briefing(query: str) -> dict[str, Any]:
    subject = extract_briefing_subject(query)
    imgs = await image_search(subject, max_results=10)
    search_raw = await web_search(subject, max_results=4)
    sources = _parse_search_sources(search_raw)
    summary = (
        f"Image results for “{subject}”. "
        f"{len(imgs)} images loaded in the center panel."
    )
    if sources:
        summary += f" {sources[0].get('snippet', '')[:200]}"
    return _briefing_shell(
        query=subject,
        title=subject.title() if subject else "Images",
        summary=summary,
        kind="images",
        images=imgs,
        sources=sources,
    )


async def build_market_briefing(query: str, symbol: str = "") -> dict[str, Any]:
    sym = symbol.strip() or "^GSPC"
    data = await get_market_quote_data(sym)
    if data.get("error"):
        text = await get_market_quote(sym)
        return _briefing_shell(
            query=query,
            title=sym,
            summary=text,
            kind="market",
            market=data,
        )
    price = data.get("price")
    name = data.get("name", sym)
    currency = data.get("currency", "USD")
    change = data.get("change")
    pct = data.get("change_pct")
    summary = f"{name} ({sym}): {price:,.2f} {currency}" if price is not None else str(data)
    if change is not None and pct is not None:
        sign = "+" if change >= 0 else ""
        summary += f" — {sign}{change:,.2f} ({sign}{pct:.2f}%)"
    if data.get("as_of"):
        summary += f" As of {data['as_of']}."
    sources = []
    if data.get("chart_url"):
        sources.append(
            {
                "title": f"Yahoo Finance — {name}",
                "url": data["chart_url"],
                "snippet": "Live chart and quote details.",
            }
        )
    return _briefing_shell(
        query=query,
        title=name,
        summary=summary,
        kind="market",
        market=data,
        sources=sources,
    )


_last_briefing: dict[str, dict[str, Any]] = {}


def pop_last_briefing(user_id: str) -> dict[str, Any] | None:
    return _last_briefing.pop(user_id, None)


async def open_web_briefing(user_id: str, briefing: dict[str, Any]) -> dict[str, Any]:
    _last_briefing[user_id] = briefing
    await publish_ws(user_id, "briefing.open", briefing)
    return briefing
