"""End-to-end pipeline tests for all three scenarios."""

from pathlib import Path

from graphic_agent.config import load_scenario, load_task
from graphic_agent.pipeline import GraphicAgentPipeline

ROOT = Path(__file__).resolve().parents[1]


def test_story_comic_pipeline(tmp_path: Path) -> None:
    scenario = load_scenario(ROOT / "configs/scenarios/story_comic.yaml")
    task = load_task(ROOT / "examples/story_comic_robot_cat.yaml")
    result = GraphicAgentPipeline(scenario, tmp_path / "story").run(task)

    assert result.revision.action == "accept"
    assert Path(result.final_image).exists()
    assert (tmp_path / "story/reports/result.json").exists()

    # Evaluators actually ran
    assert "asset_completeness" in result.critique.evaluator_names
    assert "narrative_consistency" in result.critique.evaluator_names
    assert "image_size" in result.critique.evaluator_names
    assert "file_sanity" in result.critique.evaluator_names

    # Cost tracking
    assert result.cost_summary.total_generation_calls == len(result.generated_assets)
    assert result.cost_summary.total_rounds == result.rounds_completed
    assert all(v >= 1 for v in result.cost_summary.per_asset_calls.values())

    # Context memory populated with character reference
    assert len(result.context_memory.reference_image_paths) > 0

    # Depends_on: panels depend on character_reference
    panels = [s for s in result.planned_assets if s.type == "panel"]
    refs = [s for s in result.planned_assets if s.type == "character_reference"]
    assert len(refs) > 0
    for panel in panels:
        assert refs[0].id in panel.depends_on


def test_game_assets_pipeline(tmp_path: Path) -> None:
    scenario = load_scenario(ROOT / "configs/scenarios/game_assets.yaml")
    task = load_task(ROOT / "examples/game_assets_fantasy_rpg.yaml")
    result = GraphicAgentPipeline(scenario, tmp_path / "game").run(task)

    assert result.revision.action == "accept"
    assert len(result.generated_assets) == 10
    assert Path(result.final_image).exists()

    # All 5 categories covered
    categories = {s.category for s in result.planned_assets}
    assert categories == {"characters", "environments", "props", "icons", "ui_elements"}

    # Cost tracking
    assert result.cost_summary.total_generation_calls == 10
    assert result.cost_summary.total_retry_calls == 0


def test_concept_art_board_pipeline(tmp_path: Path) -> None:
    scenario = load_scenario(ROOT / "configs/scenarios/concept_art_board.yaml")
    task = load_task(ROOT / "examples/concept_art_cyberpunk_hero.yaml")
    result = GraphicAgentPipeline(scenario, tmp_path / "concept").run(task)

    assert result.revision.action == "accept"
    assert Path(result.final_image).exists()

    # 2 subjects x 4 variations = 8 assets
    assert len(result.planned_assets) == 8
    assert len(result.generated_assets) == 8

    # Categories match subjects
    categories = {s.category for s in result.planned_assets}
    assert categories == {"character", "environment"}

    # Reports saved
    assert (tmp_path / "concept/reports/cost_summary.json").exists()
    assert (tmp_path / "concept/reports/context_memory.json").exists()
