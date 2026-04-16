from planner.context import build_planning_context


def test_build_planning_context_basic():
    goal = "Build an autonomous execution plan"
    memory = {}
    
    context = build_planning_context(goal, memory)
    
    assert context["goal"] == goal
    assert context["memory_entries"] == {}
    assert context["recent_summary"] is None
    assert context["memory_insights"] == []


def test_build_planning_context_with_memory():
    goal = "Build something"
    memory = {
        "goal": {"goal": "Build an autonomous execution plan"},
        "summary": {"confidence": 0.7, "risk_level": "high"}
    }
    
    context = build_planning_context(goal, memory)
    
    assert any("Similar goal found in memory" in insight for insight in context["memory_insights"])
    assert "Previous high-risk action detected" in context["memory_insights"]
    assert "Previous run had low confidence" in context["memory_insights"]


def test_build_planning_context_with_recent_summary():
    goal = "Test goal"
    memory = {}
    recent_summary = {"repair_used": True, "confidence": 0.5}
    
    context = build_planning_context(goal, memory, recent_summary)
    
    assert "Recent run required repairs" in context["memory_insights"]
    assert "Recent run had reduced confidence" in context["memory_insights"]
