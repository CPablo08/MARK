"""Built-in MARK tools — imported at API startup to populate the registry."""

from mark_tools.registry import register_tool


@register_tool("memory_search", "Search the user's memory vault", {"memory", "read"})
async def memory_search(query: str) -> str:
    return f"memory_search:{query}"


@register_tool("memory_store", "Store a note in memory", {"memory", "write"})
async def memory_store(content: str, category: str = "semantic") -> str:
    return f"memory_store:{category}:{content[:80]}"


@register_tool("run_task", "Queue a full autonomous MARK task", {"agent", "write"})
async def run_task(objective: str, title: str = "User task") -> str:
    return f"run_task:{title}:{objective[:120]}"


@register_tool("list_agents", "List active agent instances", {"agent", "read"})
async def list_agents() -> str:
    return "list_agents"


@register_tool(
    "visualize",
    "Open HTML/charts in the center workspace panel (Visualize plugin)",
    {"visualize", "write"},
)
async def visualize_stub(title: str = "", html: str = "") -> str:
    return f"visualize:{title}"


@register_tool(
    "cam",
    "Open Cam skill: live camera + CV in center; chat collapses at bottom",
    {"cam", "skill"},
)
async def cam_stub(objective: str = "") -> str:
    return f"cam:{objective}"
