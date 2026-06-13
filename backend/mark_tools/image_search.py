"""Playwright image search (DuckDuckGo Images) — no API key."""

from __future__ import annotations

import re
from typing import Any
from urllib.parse import quote_plus

from mark_tools.browser import get_browser


async def image_search(query: str, max_results: int = 10) -> list[dict[str, Any]]:
    """Return image results: url, thumb_url, title, source_url."""
    q = query.strip()
    if not q:
        return []
    max_results = max(1, min(max_results, 12))

    browser = await get_browser()
    if not browser:
        return []

    try:
        page = await browser.new_page()
        await page.goto(
            f"https://duckduckgo.com/?q={quote_plus(q)}&iax=images&ia=images",
            timeout=28000,
            wait_until="domcontentloaded",
        )
        await page.wait_for_timeout(1200)
        items = await page.evaluate(
            """(limit) => {
              const out = [];
              const seen = new Set();
              const tiles = document.querySelectorAll(
                'img[src], a[data-id] img, .tile--img img, figure img'
              );
              for (const img of tiles) {
                if (out.length >= limit) break;
                let src = img.currentSrc || img.src || '';
                if (!src || src.startsWith('data:') || seen.has(src)) continue;
                const w = img.naturalWidth || img.width || 0;
                const h = img.naturalHeight || img.height || 0;
                if (w > 0 && w < 80) continue;
                seen.add(src);
                const link = img.closest('a');
                const source = link && link.href ? link.href : '';
                const title = img.alt || img.title || '';
                out.push({
                  url: src,
                  thumb_url: src,
                  title: title.slice(0, 200),
                  source_url: source,
                  width: w,
                  height: h,
                });
              }
              if (out.length < 3) {
                document.querySelectorAll('a[href*="external-content"]').forEach(a => {
                  if (out.length >= limit) return;
                  const im = a.querySelector('img');
                  if (!im) return;
                  const src = im.src || '';
                  if (!src || seen.has(src)) return;
                  seen.add(src);
                  out.push({
                    url: src,
                    thumb_url: src,
                    title: (im.alt || '').slice(0, 200),
                    source_url: a.href || '',
                    width: 0,
                    height: 0,
                  });
                });
              }
              return out;
            }""",
            max_results,
        )
        await page.close()
        return _normalize_items(items or [], max_results)
    except Exception:
        return []


def _normalize_items(raw: list[dict[str, Any]], limit: int) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    seen: set[str] = set()
    for item in raw:
        url = (item.get("url") or item.get("thumb_url") or "").strip()
        if not url or url in seen:
            continue
        if not url.startswith("http"):
            continue
        seen.add(url)
        out.append(
            {
                "url": url,
                "thumb_url": (item.get("thumb_url") or url).strip(),
                "title": (item.get("title") or "").strip()[:200],
                "source_url": (item.get("source_url") or "").strip(),
                "width": int(item.get("width") or 0),
                "height": int(item.get("height") or 0),
            }
        )
        if len(out) >= limit:
            break
    return out


async def image_search_text(query: str, max_results: int = 8) -> str:
    """Tool-friendly string summary."""
    rows = await image_search(query, max_results=max_results)
    if not rows:
        return f"No images found for “{query}”. Try web_search for pages with pictures."
    lines = [f"Image search: “{query}” ({len(rows)} results)\n"]
    for i, r in enumerate(rows, 1):
        lines.append(f"{i}. {r.get('title') or 'Image'}")
        lines.append(f"   {r.get('url')}")
        if r.get("source_url"):
            lines.append(f"   source: {r.get('source_url')}")
    return "\n".join(lines)
