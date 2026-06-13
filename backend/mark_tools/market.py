"""Live market quotes via Yahoo Finance (no API key required)."""

from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any

import httpx

_YAHOO_CHART = "https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
_HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; MARK/1.0)"}

# Common names → Yahoo tickers
_ALIASES: dict[str, str] = {
    "SP500": "^GSPC",
    "S&P500": "^GSPC",
    "S&P 500": "^GSPC",
    "SPX": "^GSPC",
    "GSPC": "^GSPC",
    "NASDAQ": "^IXIC",
    "NDX": "^NDX",
    "DOW": "^DJI",
    "DJIA": "^DJI",
    "BTC": "BTC-USD",
    "BITCOIN": "BTC-USD",
    "ETH": "ETH-USD",
    "ETHEREUM": "ETH-USD",
}


def _normalize_symbol(raw: str) -> str:
    text = raw.strip().upper()
    if not text:
        return "^GSPC"
    text = re.sub(r"\s+", " ", text)
    if text in _ALIASES:
        return _ALIASES[text]
    if "S&P" in text or "SP 500" in text:
        return "^GSPC"
    if text.startswith("^"):
        return text
    if "-" in text or "." in text:
        return text
    return text


async def get_market_quote_data(symbol: str = "^GSPC") -> dict[str, Any]:
    """Structured quote for Research panel market card."""
    ticker = _normalize_symbol(symbol)
    encoded = ticker.replace("^", "%5E")

    async with httpx.AsyncClient(timeout=20, headers=_HEADERS) as client:
        r = await client.get(_YAHOO_CHART.format(symbol=encoded))
        if r.status_code == 404:
            return {"error": f"No quote for {symbol}", "symbol": ticker}
        r.raise_for_status()
        data = r.json()

    result = data.get("chart", {}).get("result")
    if not result:
        return {"error": "Could not parse quote", "symbol": ticker}

    meta = result[0].get("meta", {})
    price = meta.get("regularMarketPrice")
    prev = meta.get("chartPreviousClose") or meta.get("previousClose")
    currency = meta.get("currency", "USD")
    name = meta.get("shortName") or meta.get("symbol") or ticker
    ts = meta.get("regularMarketTime")

    change = (price - prev) if price is not None and prev is not None else None
    pct = (change / prev * 100) if change is not None and prev else None
    when = ""
    if ts:
        when = datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    return {
        "symbol": ticker,
        "name": name,
        "price": price,
        "currency": currency,
        "change": change,
        "change_pct": pct,
        "as_of": when,
        "market_state": meta.get("marketState", ""),
        "chart_url": f"https://finance.yahoo.com/quote/{ticker}",
    }


async def get_market_quote(symbol: str = "^GSPC") -> str:
    """Fetch latest price for a stock, index, or crypto ticker."""
    ticker = _normalize_symbol(symbol)
    encoded = ticker.replace("^", "%5E")

    async with httpx.AsyncClient(timeout=20, headers=_HEADERS) as client:
        r = await client.get(_YAHOO_CHART.format(symbol=encoded))
        if r.status_code == 404:
            return f"No quote found for “{symbol}”. Try a Yahoo ticker like AAPL, ^GSPC, or BTC-USD."
        r.raise_for_status()
        data = r.json()

    result = data.get("chart", {}).get("result")
    if not result:
        return f"Could not parse a quote for “{symbol}”."

    meta = result[0].get("meta", {})
    price = meta.get("regularMarketPrice")
    prev = meta.get("chartPreviousClose") or meta.get("previousClose")
    currency = meta.get("currency", "USD")
    name = meta.get("shortName") or meta.get("symbol") or ticker
    market_state = meta.get("marketState", "")
    ts = meta.get("regularMarketTime")

    if price is None:
        return f"No live price available for {name} ({ticker}) right now."

    change = (price - prev) if prev is not None else None
    pct = (change / prev * 100) if change is not None and prev else None

    when = ""
    if ts:
        when = datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    lines = [
        f"{name} ({ticker}): **{price:,.2f} {currency}**",
    ]
    if change is not None and pct is not None:
        sign = "+" if change >= 0 else ""
        lines.append(f"Change: {sign}{change:,.2f} ({sign}{pct:.2f}%) vs prior close")
    if market_state:
        lines.append(f"Market state: {market_state}")
    if when:
        lines.append(f"As of: {when}")
    lines.append("(Source: Yahoo Finance — delayed quotes, not for trading decisions.)")
    return "\n".join(lines)
