from pathlib import Path

import pytest

from graphic_agent.config import load_provider_profile, load_scenario
from graphic_agent.costing import estimate_run_budget

ROOT = Path(__file__).resolve().parents[1]


def test_mock_provider_budget_is_free() -> None:
    scenario = load_scenario(ROOT / "configs/scenarios/story_comic.yaml")
    profile = load_provider_profile(ROOT / "configs/providers/mock.yaml")

    estimate = estimate_run_budget(scenario, profile, planned_asset_count=5)

    assert estimate.provider_profile == "mock"
    assert estimate.baseline_total_usd == 0
    assert estimate.with_retry_buffer_usd == 0
    assert estimate.components["image_generation_usd"] == 0


def test_openai_budget_includes_components_and_retry_buffer() -> None:
    scenario = load_scenario(ROOT / "configs/scenarios/story_comic.yaml")
    profile = load_provider_profile(ROOT / "configs/providers/openai_compatible.yaml")

    estimate = estimate_run_budget(scenario, profile, planned_asset_count=5)

    assert estimate.components["planner_usd"] == pytest.approx(0.002)
    assert estimate.components["critic_usd"] == pytest.approx(0.004)
    assert estimate.components["image_generation_usd"] == pytest.approx(0.265)
    assert estimate.components["retry_buffer_usd"] == pytest.approx(0.53)
    assert estimate.baseline_total_usd == pytest.approx(0.271)
    assert estimate.with_retry_buffer_usd == pytest.approx(0.801)


@pytest.mark.parametrize(
    ("scenario_file", "planned_asset_count", "retry_buffer_asset_count"),
    [
        ("story_comic.yaml", 5, 10),
        ("game_assets.yaml", 10, 20),
        ("concept_art_board.yaml", 8, 8),
    ],
)
def test_budget_estimate_supports_all_demo_scenarios(
    scenario_file: str,
    planned_asset_count: int,
    retry_buffer_asset_count: int,
) -> None:
    scenario = load_scenario(ROOT / f"configs/scenarios/{scenario_file}")
    profile = load_provider_profile(ROOT / "configs/providers/openai_compatible.yaml")

    estimate = estimate_run_budget(scenario, profile, planned_asset_count)

    assert estimate.planned_asset_count == planned_asset_count
    assert estimate.retry_buffer_asset_count == retry_buffer_asset_count
