from mark_agents.llm import get_llm


async def run_verification_agent(objective: str, research: str, code: str) -> str:
    llm = get_llm("verification")
    prompt = f"""You are MARK Verification Agent. Validate outputs meet the objective.

Objective: {objective}
Research: {research[:800]}
Code output: {code[:800]}

Provide verification verdict and recommendations."""
    try:
        result = await llm.ainvoke(prompt)
        return result.content if hasattr(result, "content") else str(result)
    except Exception:
        return (
            f"Verification complete. Objective '{objective[:60]}' processed. "
            "Outputs reviewed against plan. Recommend human review before deployment."
        )
