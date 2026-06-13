"""MCP host — stdio MCP servers from Plugins, exposed to chat as LangChain tools."""

from __future__ import annotations

import asyncio
import logging
import os
import re
from contextlib import AsyncExitStack
from typing import Any

from langchain_core.tools import StructuredTool
from mcp import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client
from pydantic import Field, create_model

from mark_core.config import get_settings

logger = logging.getLogger("mark.mcp")

_servers: dict[str, McpServerConnection] = {}
_tool_catalog: list[dict[str, Any]] = []
_reload_lock = asyncio.Lock()


def _slug(name: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "_", (name or "mcp").lower()).strip("_")
    return s or "mcp"


def _merge_env(config_env: dict[str, str] | None) -> dict[str, str]:
    env = {k: v for k, v in os.environ.items() if isinstance(v, str)}
    settings = get_settings()
    if settings.github_token:
        env.setdefault("GITHUB_TOKEN", settings.github_token)
    if settings.openai_api_key:
        env.setdefault("OPENAI_API_KEY", settings.openai_api_key)
    if config_env:
        for key, val in config_env.items():
            if val is not None:
                env[str(key)] = str(val)
    return env


def _tool_result_text(result: Any) -> str:
    parts: list[str] = []
    for block in getattr(result, "content", None) or []:
        text = getattr(block, "text", None)
        if text:
            parts.append(text)
        elif isinstance(block, dict) and block.get("type") == "text":
            parts.append(str(block.get("text", "")))
    if parts:
        return "\n".join(parts)
    if getattr(result, "isError", False):
        return f"MCP error: {result}"
    return str(result)


def _json_schema_to_fields(schema: dict[str, Any]) -> dict[str, Any]:
    props = schema.get("properties") if isinstance(schema, dict) else None
    if not props:
        return {}
    required = set(schema.get("required") or [])
    fields: dict[str, Any] = {}
    type_map = {
        "string": str,
        "integer": int,
        "number": float,
        "boolean": bool,
        "array": list,
        "object": dict,
    }
    for pname, pschema in props.items():
        if not isinstance(pschema, dict):
            continue
        py_type = type_map.get(pschema.get("type", "string"), str)
        desc = pschema.get("description") or ""
        if pname in required:
            fields[pname] = (py_type, Field(description=desc))
        else:
            fields[pname] = (py_type | None, Field(default=None, description=desc))
    return fields


class McpServerConnection:
    def __init__(self, slug: str, display_name: str, config: dict[str, Any]) -> None:
        self.slug = slug
        self.display_name = display_name
        self.config = config
        self._stack = AsyncExitStack()
        self.session: ClientSession | None = None
        self.tools: list[Any] = []

    async def connect(self) -> None:
        command = self.config.get("command") or "npx"
        args = list(self.config.get("args") or [])
        if command == "npx" and args and args[0] not in ("-y", "-yq", "--yes"):
            args = ["-y", *args]

        params = StdioServerParameters(
            command=str(command),
            args=[str(a) for a in args],
            env=_merge_env(self.config.get("env")),
        )
        read, write = await self._stack.enter_async_context(stdio_client(params))
        session = await self._stack.enter_async_context(ClientSession(read, write))
        await session.initialize()
        listed = await session.list_tools()
        self.session = session
        self.tools = list(listed.tools)
        logger.info(
            "MCP connected: %s (%d tools)",
            self.display_name,
            len(self.tools),
        )

    async def call_tool(self, tool_name: str, arguments: dict[str, Any]) -> str:
        if not self.session:
            return f"MCP server “{self.display_name}” is not connected."
        try:
            result = await self.session.call_tool(tool_name, arguments=arguments or {})
            return _tool_result_text(result)[:12000]
        except Exception as e:
            logger.warning("MCP tool %s.%s failed: %s", self.slug, tool_name, e)
            return f"MCP tool error: {e}"

    async def close(self) -> None:
        self.session = None
        self.tools = []
        await self._stack.aclose()
        self._stack = AsyncExitStack()


def _qualified_name(slug: str, tool_name: str) -> str:
    return f"{slug}__{tool_name}"


def _rebuild_catalog() -> None:
    global _tool_catalog
    catalog: list[dict[str, Any]] = []
    for slug, conn in _servers.items():
        for t in conn.tools:
            name = getattr(t, "name", "tool")
            catalog.append(
                {
                    "name": _qualified_name(slug, name),
                    "original_name": name,
                    "server": conn.display_name,
                    "slug": slug,
                    "description": (getattr(t, "description", None) or name)[:500],
                    "tags": {"mcp", "network", "read"},
                }
            )
    _tool_catalog = catalog


async def reload_mcp_servers(configs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Connect to enabled MCP servers (stdio). Replaces previous connections."""
    async with _reload_lock:
        for conn in list(_servers.values()):
            try:
                await conn.close()
            except Exception as e:
                logger.warning("MCP close error: %s", e)
        _servers.clear()

        for cfg in configs:
            name = cfg.get("name", "MCP")
            slug = _slug(name)
            if slug in _servers:
                slug = f"{slug}_{len(_servers)}"
            conn = McpServerConnection(slug, name, cfg)
            try:
                await asyncio.wait_for(conn.connect(), timeout=180.0)
                _servers[slug] = conn
            except Exception as e:
                logger.warning("Failed to connect MCP “%s”: %s", name, e)
                try:
                    await conn.close()
                except Exception:
                    pass

        _rebuild_catalog()
        return list_mcp_tools()


def load_mcp_servers(configs: list[dict]) -> list[dict[str, Any]]:
    """Sync entrypoint used from integrations routes — schedules async reload."""
    try:
        loop = asyncio.get_running_loop()
        loop.create_task(reload_mcp_servers(configs))
    except RuntimeError:
        asyncio.run(reload_mcp_servers(configs))
    return list_mcp_tools()


def list_mcp_tools() -> list[dict[str, Any]]:
    return list(_tool_catalog)


async def invoke_mcp_tool(tool_name: str, args: dict[str, Any]) -> str:
    if "__" not in tool_name:
        return f"Unknown MCP tool: {tool_name}"
    slug, original = tool_name.split("__", 1)
    conn = _servers.get(slug)
    if not conn:
        return f"MCP server for “{tool_name}” is not connected. Check Plugins."
    return await conn.call_tool(original, args)


async def shutdown_mcp_servers() -> None:
    async with _reload_lock:
        for conn in list(_servers.values()):
            await conn.close()
        _servers.clear()
        _rebuild_catalog()


def build_mcp_langchain_tools() -> list[StructuredTool]:
    """LangChain tools for all connected MCP servers."""
    lc_tools: list[StructuredTool] = []

    for slug, conn in _servers.items():
        for tdef in conn.tools:
            original = getattr(tdef, "name", "tool")
            qualified = _qualified_name(slug, original)
            description = (
                f"[{conn.display_name}] {getattr(tdef, 'description', None) or original}"
            )[:600]
            schema = getattr(tdef, "inputSchema", None) or {}
            fields = _json_schema_to_fields(schema if isinstance(schema, dict) else {})
            args_schema = (
                create_model(f"Mcp_{slug}_{original}".replace("-", "_"), **fields)
                if fields
                else create_model(f"Mcp_{slug}_{original}".replace("-", "_"))
            )

            async def _run(
                _slug: str = slug,
                _tool: str = original,
                **kwargs: Any,
            ) -> str:
                clean = {k: v for k, v in kwargs.items() if v is not None}
                return await invoke_mcp_tool(f"{_slug}__{_tool}", clean)

            lc_tools.append(
                StructuredTool.from_function(
                    coroutine=_run,
                    name=qualified,
                    description=description,
                    args_schema=args_schema,
                )
            )

    return lc_tools


async def build_mcp_langchain_tools_async() -> list[StructuredTool]:
    return build_mcp_langchain_tools()
