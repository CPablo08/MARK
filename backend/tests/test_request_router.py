"""Router classification tests (no Playwright)."""

from mark_agents.request_router import route_request_rules


def test_market_not_research():
    plan = route_request_rules("what is the current price of the S&P 500")
    assert plan.kind == "market_briefing"
    assert plan.symbol == "^GSPC"


def test_image_briefing():
    plan = route_request_rules("find me a picture of Iron Man Mark II armor")
    assert plan.kind == "image_briefing"


def test_research_briefing():
    plan = route_request_rules("who is Leonardo DiCaprio")
    assert plan.kind == "research_briefing"


def test_llm_fallback():
    plan = route_request_rules("draft an email to my team about the offsite")
    assert plan.kind == "llm"
