from mark_tools.browser import web_research, web_search


async def run_browser_agent(objective: str) -> str:
    try:
        return await web_research(objective)
    except Exception:
        try:
            return await web_search(objective, max_results=4)
        except Exception as e:
            return f"Browser agent: search fallback ({e})"
