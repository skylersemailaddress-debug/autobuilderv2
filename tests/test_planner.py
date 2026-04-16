from planner.planner import Planner


def test_planner_returns_three_tasks():
    planner = Planner()
    tasks = planner.create_plan("deliver value")

    assert len(tasks) == 3
    assert tasks[0].title == "Analyze goal: deliver value"
    assert tasks[1].title == "Generate artifact"
    assert tasks[2].title == "Validate output"
