from mark_agents.llm import get_llm


async def run_planner_agent(objective: str, context: str) -> str:
    try:
        llm = get_llm("planner")
        prompt = f"""You are MARK Planner Agent. Decompose this objective into 3-5 concrete subtasks.

Context from memory:
{context or "None"}

Objective:
{objective}

Return a numbered execution plan."""
        result = await llm.ainvoke(prompt)
        return result.content if hasattr(result, "content") else str(result)
    except Exception as e:
        return (
            f"1. Analyze objective: {objective[:80]}\n"
            f"2. Research domain and constraints\n"
            f"3. Execute solution steps\n"
            f"4. Verify outputs\n"
            f"5. Document results\n"
            f"(Planner fallback: {e})"
        )
