from dataclasses import dataclass
from typing import Callable, Any


@dataclass
class ToolDef:
    name: str
    description: str
    tags: set[str]
    handler: Callable[..., Any]


TOOLS: dict[str, ToolDef] = {}


def register_tool(name: str, description: str, tags: set[str]):
    def decorator(fn):
        TOOLS[name] = ToolDef(name=name, description=description, tags=tags, handler=fn)
        return fn
    return decorator


def get_tool(name: str) -> ToolDef | None:
    return TOOLS.get(name)
