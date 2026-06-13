from mark_agents.llm import get_llm
from mark_tools.sandbox import run_sandbox_code


async def run_coding_agent(objective: str, plan: str) -> str:
    llm = get_llm("coding")
    prompt = f"""You are MARK Coding Agent. Write minimal Python to demonstrate progress on:

Objective: {objective}
Plan: {plan}

Return only executable Python code, no markdown fences."""
    try:
        result = await llm.ainvoke(prompt)
        code = result.content if hasattr(result, "content") else str(result)
        code = code.replace("```python", "").replace("```", "").strip()
        output = await run_sandbox_code(code)
        return f"Generated code executed.\nOutput: {output}\n\nCode:\n{code[:500]}"
    except Exception as e:
        return f"Coding agent stub output for: {objective[:100]} ({e})"
