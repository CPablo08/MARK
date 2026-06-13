from mark_agents.llm import get_llm
from mark_tools.browser import web_research, web_search


async def run_research_agent(objective: str, plan: str) -> str:
    search_results = await web_search(objective, max_results=6)
    deep = ""
    try:
        deep = await web_research(objective)
    except Exception:
        deep = search_results
    llm = get_llm("research")
    prompt = f"""You are MARK Research Agent. Synthesize findings.

Objective: {objective}
Plan: {plan}
Search results: {search_results}

Deep read: {deep[:2500]}

Provide a concise research summary with key insights, data points, and caveats."""
    try:
        result = await llm.ainvoke(prompt)
        return result.content if hasattr(result, "content") else str(result)
    except Exception:
        return f"Research summary (offline mode):\n{search_results}"
