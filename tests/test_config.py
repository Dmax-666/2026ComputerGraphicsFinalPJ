from pathlib import Path

import pytest

from graphic_agent.config import (
    load_provider_profile,
    load_scenario,
    load_task,
    resolve_provider_profile,
)

ROOT = Path(__file__).resolve().parents[1]


def test_load_story_comic_scenario() -> None:
    scenario = load_scenario(ROOT / "configs/scenarios/story_comic.yaml")
    assert scenario.name == "story_comic"
    assert scenario.render.type == "comic_page"
    assert scenario.revision.max_rounds == 3
    assert "image_size" in scenario.evaluators
    assert "file_sanity" in scenario.evaluators


def test_load_game_assets_scenario() -> None:
    scenario = load_scenario(ROOT / "configs/scenarios/game_assets.yaml")
    assert scenario.name == "game_assets"
    assert scenario.render.type == "asset_sheet"
    assert "category_coverage" in scenario.evaluators


def test_load_concept_art_board_scenario() -> None:
    scenario = load_scenario(ROOT / "configs/scenarios/concept_art_board.yaml")
    assert scenario.name == "concept_art_board"
    assert scenario.render.type == "asset_sheet"
    assert scenario.assets["variations_per_subject"] == 4
    assert scenario.assets["subjects"] == ["character", "environment"]


def test_load_example_task() -> None:
    task = load_task(ROOT / "examples/story_comic_robot_cat.yaml")
    assert task.title == "Robot and the Lost Cat"
    assert "robot" in task.prompt.lower()


def test_load_concept_art_task() -> None:
    task = load_task(ROOT / "examples/concept_art_cyberpunk_hero.yaml")
    assert task.title == "Cyberpunk Hero Concept Exploration"
    assert "cyberpunk" in task.prompt.lower()


def test_load_mock_provider_profile() -> None:
    profile = load_provider_profile(ROOT / "configs/providers/mock.yaml")

    assert profile.name == "mock"
    assert profile.models["planner"].provider == "mock"
    assert profile.models["critic"].model == "mock-vision-critic"
    assert profile.models["image"].model == "mock-image-generator"


@pytest.mark.parametrize(
    "filename",
    [
        "mock.yaml",
        "openai_compatible.yaml",
        "google.yaml",
        "dashscope.yaml",
        "deepseek.yaml",
        "anthropic.yaml",
    ],
)
def test_builtin_provider_profiles_load(filename: str) -> None:
    profile = load_provider_profile(ROOT / f"configs/providers/{filename}")

    assert profile.name
    assert profile.models
    assert profile.pricing["source_checked_at"]


def test_resolve_provider_profile_by_name() -> None:
    profile = resolve_provider_profile("openai_compatible", ROOT / "configs/providers")

    assert profile.name == "openai_compatible"
    assert profile.models["planner"].model == "gpt-5.4-mini"


def test_provider_profile_rejects_missing_role_mappings(tmp_path: Path) -> None:
    profile_path = tmp_path / "missing_roles.yaml"
    profile_path.write_text(
        """
name: bad
models: {}
""",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="model role mapping"):
        load_provider_profile(profile_path)


def test_provider_profile_rejects_unknown_provider(tmp_path: Path) -> None:
    profile_path = tmp_path / "bad_provider.yaml"
    profile_path.write_text(
        """
name: bad
models:
  planner:
    provider: made_up
    model: mock-planner
""",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="Unknown provider"):
        load_provider_profile(profile_path)


def test_provider_profile_rejects_missing_model_version(tmp_path: Path) -> None:
    profile_path = tmp_path / "missing_model.yaml"
    profile_path.write_text(
        """
name: bad
models:
  planner:
    provider: mock
    model: ""
""",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="model version"):
        load_provider_profile(profile_path)
