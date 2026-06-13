"""Proxy external images for the Research panel (hotlink / CORS)."""

from __future__ import annotations

import re
from urllib.parse import urlparse

import httpx
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import Response

from mark_core.auth import decode_access_token

router = APIRouter(prefix="/media", tags=["media"])

_HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; MARK/1.0)",
    "Accept": "image/*,*/*;q=0.8",
}

_ALLOWED_HOST_SUFFIXES = (
    "wikipedia.org",
    "wikimedia.org",
    "duckduckgo.com",
    "bing.com",
    "googleusercontent.com",
    "gstatic.com",
    "yahoo.com",
    "ytimg.com",
    "marvel.com",
    "fandom.com",
    "alamy.com",
    "pinimg.com",
    "imgur.com",
    "cloudfront.net",
    "amazonaws.com",
)


def _host_allowed(host: str) -> bool:
    host = host.lower()
    if not host or host in ("localhost", "127.0.0.1") or host.endswith(".local"):
        return False
    if host.replace(".", "").isdigit():
        return False
    if any(host == s or host.endswith("." + s) for s in _ALLOWED_HOST_SUFFIXES):
        return True
    # Image search returns many CDNs — allow public HTTPS hosts with a TLD
    return "." in host and not host.startswith("192.168.") and not host.startswith("10.")


@router.get("/proxy")
async def proxy_image(
    url: str = Query(..., min_length=10, max_length=2048),
    token: str | None = Query(None),
):
    if token:
        uid = decode_access_token(token)
        if not uid:
            raise HTTPException(401, "Invalid token")
    else:
        raise HTTPException(401, "Missing token query param for image proxy")
    if not url.startswith(("http://", "https://")):
        raise HTTPException(400, "Invalid URL")
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        raise HTTPException(400, "Invalid URL")
    if not _host_allowed(parsed.hostname or ""):
        raise HTTPException(403, "Host not allowed for image proxy")

    try:
        async with httpx.AsyncClient(
            timeout=15, headers=_HEADERS, follow_redirects=True
        ) as client:
            r = await client.get(url)
            r.raise_for_status()
            body = r.content
            if len(body) > 5_000_000:
                raise HTTPException(413, "Image too large")
            ctype = r.headers.get("content-type", "image/jpeg")
            if not ctype.startswith("image/"):
                if "octet-stream" not in ctype:
                    raise HTTPException(415, "Not an image")
                ctype = "image/jpeg"
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(502, f"Could not fetch image: {e}") from e

    return Response(
        content=body,
        media_type=re.split(r";\s*", ctype)[0],
        headers={"Cache-Control": "public, max-age=86400"},
    )
