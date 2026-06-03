"""End-to-end pipeline tests for all three scenarios."""

from pathlib import Path

from PIL import Image

from graphic_agent.config import load_provider_profile, load_scenario, load_task
from graphic_agent.pipeline import GraphicAgentPipeline
from graphic_agent.schemas import (
    AssetSpec,
    GeneratedAsset,
    ProviderProfile,
    ProviderUsage,
    StyleGuide,
)

ROOT = Path(__file__).resolve().parents[1]


class FakeOpenAICompatibleImageGenerator:
    def __init__(self, provider_profile: ProviderProfile) -> None:
        self.provider_profile = provider_profile

    def generate(
        self,
        spec: AssetSpec,
        style_guide: StyleGuide,
        output_dir: Path,
        round_index: int = 1,
    ) -> GeneratedAsset:
        output_dir.mkdir(parents=True, exist_ok=True)
        width, height = spec.size
        path = output_dir / f"{spec.order:03d}_{spec.id}_fake_openai.png"
        Image.new("RGB", (width, height), (80, 120, 160)).save(path)
        usage = ProviderUsage(
            role="image",
            provider_profile=self.provider_profile.name,
            provider=self.provider_profile.models["image"].provider,
            model=self.provider_profile.models["image"].model,
            image_generations=1,
            estimated_cost_usd=0.053,
        )
        return GeneratedAsset(
            spec_id=spec.id,
            path=str(path),
            prompt=spec.prompt,
            seed=round_index,
            round_index=round_index,
            metadata={
                "provider": self.provider_profile.name,
                "provider_usage": usage.model_dump(mode="json"),
            },
        )


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


def test_pipeline_accepts_openai_compatible_image_generator(tmp_path: Path) -> None:
    scenario = load_scenario(ROOT / "configs/scenarios/story_comic.yaml")
    task = load_task(ROOT / "examples/story_comic_robot_cat.yaml")
    profile = load_provider_profile(ROOT / "configs/providers/openai_compatible.yaml")
    image_generator = FakeOpenAICompatibleImageGenerator(profile)

    result = GraphicAgentPipeline(
        scenario,
        tmp_path / "real_provider",
        provider_profile=profile,
        image_generator=image_generator,
    ).run(task)

    assert result.revision.action == "accept"
    assert (tmp_path / "real_provider/reports/result.json").exists()
    assert (tmp_path / "real_provider/reports/cost_summary.json").exists()
    assert result.cost_summary.provider_usage
    assert result.cost_summary.provider_usage[0].provider_profile == "openai_compatible"
