from pathlib import Path

from graphic_agent.config import load_scenario, load_task

ROOT = Path(__file__).resolve().parents[1]


def test_load_story_comic_scenario() -> None:
    scenario = load_scenario(ROOT / "configs/scenarios/story_comic.yaml")
    assert scenario.name == "story_comic"
    assert scenario.render.type == "comic_page"
    assert scenario.revision.max_rounds == 3


def test_load_example_task() -> None:
    task = load_task(ROOT / "examples/story_comic_robot_cat.yaml")
    assert task.title == "Robot and the Lost Cat"
    assert "robot" in task.prompt.lower()
