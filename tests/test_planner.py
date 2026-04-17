from planner.planner import Planner


def test_planner_returns_three_tasks():
    planner = Planner()
    result = planner.create_plan("deliver value")

    assert len(result["tasks"]) == 3
    assert result["tasks"][0].title == "Analyze goal: deliver value"
    assert "Generate artifact" in result["tasks"][1].title
    assert "Validate output" in result["tasks"][2].title
