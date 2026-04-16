from planner.planner import Planner


def test_planner_create_plan_without_context():
    planner = Planner()
    result = planner.create_plan("Build something")
    
    assert "tasks" in result
    assert "metadata" in result
    assert len(result["tasks"]) == 3
    assert result["metadata"]["memory_used"] is False
    assert result["metadata"]["memory_insights"] == []


def test_planner_create_plan_with_context():
    planner = Planner()
    context = {
        "goal": "Build something",
        "memory_insights": ["Previous run had low confidence", "Similar goal found"]
    }
    
    result = planner.create_plan("Build something", context)
    
    assert result["metadata"]["memory_used"] is True
    assert len(result["metadata"]["memory_insights"]) == 2
    assert result["tasks"][0].result is not None
    assert "memory_context" in result["tasks"][0].result
    assert "insights" in result["tasks"][0].result
