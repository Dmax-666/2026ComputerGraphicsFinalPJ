from pathlib import Path

from graphic_agent.config import load_scenario, load_task
from graphic_agent.pipeline import GraphicAgentPipeline

ROOT = Path(__file__).resolve().parents[1]


def test_story_comic_pipeline_outputs_final_image(tmp_path: Path) -> None:
    scenario = load_scenario(ROOT / "configs/scenarios/story_comic.yaml")
    task = load_task(ROOT / "examples/story_comic_robot_cat.yaml")
    result = GraphicAgentPipeline(scenario, tmp_path / "story").run(task)
    assert result.revision.action == "accept"
    assert Path(result.final_image).exists()
    assert (tmp_path / "story/reports/result.json").exists()


def test_game_assets_pipeline_outputs_final_image(tmp_path: Path) -> None:
    scenario = load_scenario(ROOT / "configs/scenarios/game_assets.yaml")
    task = load_task(ROOT / "examples/game_assets_fantasy_rpg.yaml")
    result = GraphicAgentPipeline(scenario, tmp_path / "game").run(task)
    assert result.revision.action == "accept"
    assert len(result.generated_assets) == 10
    assert Path(result.final_image).exists()
