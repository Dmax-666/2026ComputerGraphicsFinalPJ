from pathlib import Path

import pytest

from graphic_agent.config import load_provider_profile, load_scenario
from graphic_agent.costing import (
    estimate_run_budget,
    record_generated_assets,
    record_provider_usage,
)
from graphic_agent.schemas import CostSummary, GeneratedAsset, ProviderUsage

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


def test_provider_usage_accumulates_in_cost_summary() -> None:
    summary = CostSummary()
    usage = ProviderUsage(
        role="critic",
        provider_profile="openai_compatible",
        provider="openai_compatible",
        model="gpt-5.4",
        prompt_tokens=1200,
        completion_tokens=300,
        image_generations=0,
        vision_calls=1,
        estimated_cost_usd=0.004,
    )

    record_provider_usage(summary, usage)

    assert summary.total_prompt_tokens == 1200
    assert summary.total_completion_tokens == 300
    assert summary.total_vision_calls == 1
    assert summary.estimated_cost_usd == pytest.approx(0.004)
    assert summary.provider_usage == [usage]


def test_generated_assets_increment_cost_summary_without_usage_metadata() -> None:
    summary = CostSummary()
    assets = [
        GeneratedAsset(spec_id="a1", path="a1.png", prompt="p", seed=1),
        GeneratedAsset(spec_id="a2", path="a2.png", prompt="p", seed=2),
    ]

    record_generated_assets(summary, assets, is_retry=False)

    assert summary.total_generation_calls == 2
    assert summary.total_image_generations == 2
    assert summary.total_retry_calls == 0
    assert summary.per_asset_calls == {"a1": 1, "a2": 1}


def test_generated_assets_merge_provider_usage_metadata() -> None:
    summary = CostSummary()
    asset = GeneratedAsset(
        spec_id="panel_1",
        path="panel.png",
        prompt="p",
        seed=3,
        metadata={
            "provider_usage": {
                "role": "image",
                "provider_profile": "openai_compatible",
                "provider": "openai_compatible",
                "model": "gpt-image-2",
                "image_generations": 1,
                "estimated_cost_usd": 0.053,
            }
        },
    )

    record_generated_assets(summary, [asset], is_retry=True)

    assert summary.total_generation_calls == 1
    assert summary.total_retry_calls == 1
    assert summary.total_image_generations == 1
    assert summary.estimated_cost_usd == pytest.approx(0.053)
    assert summary.provider_usage[0].role == "image"
