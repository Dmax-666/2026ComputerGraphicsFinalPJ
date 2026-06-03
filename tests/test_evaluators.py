"""Tests for the pluggable evaluator system."""

import tempfile
from pathlib import Path

from PIL import Image

from graphic_agent.evaluators.registry import get_evaluator, list_evaluators
from graphic_agent.schemas import (
    AssetSpec,
    CompositionSpec,
    GeneratedAsset,
    ScenarioConfig,
)


def _make_image(path: Path, size: tuple[int, int] = (768, 768)) -> None:
    """Create a minimal valid PNG at the given path."""
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", size, (128, 128, 128)).save(path)


def _spec(id: str = "a1", size: tuple[int, int] = (768, 768)) -> AssetSpec:
    return AssetSpec(
        id=id, type="visual", category="generic",
        title="T", description="D", purpose="P", prompt="Pr",
        size=size,
    )


def _asset(spec_id: str, path: str) -> GeneratedAsset:
    return GeneratedAsset(spec_id=spec_id, path=path, prompt="p", seed=1)


def _composition(path: str) -> CompositionSpec:
    return CompositionSpec(type="asset_sheet", page_size=(800, 800), output_path=path)


# --- Registry ---

def test_list_evaluators_contains_all_builtins() -> None:
    names = list_evaluators()
    expected = {
        "asset_completeness", "category_coverage", "character_consistency",
        "file_sanity", "image_size", "narrative_consistency",
        "style_consistency", "text_layout_quality",
    }
    assert expected.issubset(set(names))


def test_get_evaluator_unknown_raises() -> None:
    try:
        get_evaluator("nonexistent_evaluator")
        raise AssertionError("Should have raised ValueError")
    except ValueError as e:
        assert "nonexistent_evaluator" in str(e)


# --- AssetCompleteness ---

def test_asset_completeness_missing_asset() -> None:
    ev = get_evaluator("asset_completeness")
    with tempfile.TemporaryDirectory() as d:
        comp_path = Path(d) / "final.png"
        _make_image(comp_path)
        # spec exists but no generated asset
        issues = ev.evaluate(
            scenario=ScenarioConfig(name="test"),
            specs=[_spec("missing")],
            generated_assets=[],
            composition=_composition(str(comp_path)),
        )
    assert len(issues) == 1
    assert issues[0].category == "missing_asset"
    assert issues[0].severity == "high"


def test_asset_completeness_all_present() -> None:
    ev = get_evaluator("asset_completeness")
    with tempfile.TemporaryDirectory() as d:
        img_path = Path(d) / "a1.png"
        comp_path = Path(d) / "final.png"
        _make_image(img_path)
        _make_image(comp_path)
        issues = ev.evaluate(
            scenario=ScenarioConfig(name="test"),
            specs=[_spec("a1")],
            generated_assets=[_asset("a1", str(img_path))],
            composition=_composition(str(comp_path)),
        )
    assert issues == []


# --- ImageSize ---

def test_image_size_match() -> None:
    ev = get_evaluator("image_size")
    with tempfile.TemporaryDirectory() as d:
        img_path = Path(d) / "a1.png"
        comp_path = Path(d) / "final.png"
        _make_image(img_path, (768, 768))
        _make_image(comp_path)
        issues = ev.evaluate(
            scenario=ScenarioConfig(name="test"),
            specs=[_spec("a1", size=(768, 768))],
            generated_assets=[_asset("a1", str(img_path))],
            composition=_composition(str(comp_path)),
        )
    assert issues == []


def test_image_size_mismatch() -> None:
    ev = get_evaluator("image_size")
    with tempfile.TemporaryDirectory() as d:
        img_path = Path(d) / "a1.png"
        comp_path = Path(d) / "final.png"
        _make_image(img_path, (512, 512))  # wrong size
        _make_image(comp_path)
        issues = ev.evaluate(
            scenario=ScenarioConfig(name="test"),
            specs=[_spec("a1", size=(768, 768))],
            generated_assets=[_asset("a1", str(img_path))],
            composition=_composition(str(comp_path)),
        )
    assert len(issues) == 1
    assert issues[0].category == "image_size_mismatch"


# --- FileSanity ---

def test_file_sanity_ok() -> None:
    ev = get_evaluator("file_sanity")
    with tempfile.TemporaryDirectory() as d:
        img_path = Path(d) / "a1.png"
        comp_path = Path(d) / "final.png"
        _make_image(img_path)
        _make_image(comp_path)
        issues = ev.evaluate(
            scenario=ScenarioConfig(name="test"),
            specs=[_spec("a1")],
            generated_assets=[_asset("a1", str(img_path))],
            composition=_composition(str(comp_path)),
        )
    assert issues == []


def test_file_sanity_tiny_file() -> None:
    ev = get_evaluator("file_sanity")
    with tempfile.TemporaryDirectory() as d:
        img_path = Path(d) / "a1.png"
        img_path.write_bytes(b"x" * 100)  # suspiciously small
        comp_path = Path(d) / "final.png"
        _make_image(comp_path)
        issues = ev.evaluate(
            scenario=ScenarioConfig(name="test"),
            specs=[_spec("a1")],
            generated_assets=[_asset("a1", str(img_path))],
            composition=_composition(str(comp_path)),
        )
    assert len(issues) == 1
    assert issues[0].category == "file_too_small"
    assert issues[0].severity == "high"


# --- CategoryCoverage ---

def test_category_coverage_missing() -> None:
    ev = get_evaluator("category_coverage")
    with tempfile.TemporaryDirectory() as d:
        comp_path = Path(d) / "final.png"
        _make_image(comp_path)
        scenario = ScenarioConfig(
            name="test",
            assets={"categories": ["characters", "props", "icons"]},
        )
        # only 'characters' category present
        spec = _spec("c1")
        spec = spec.model_copy(update={"category": "characters"})
        issues = ev.evaluate(
            scenario=scenario,
            specs=[spec],
            generated_assets=[],
            composition=_composition(str(comp_path)),
        )
    assert len(issues) == 1
    assert "props" in issues[0].message or "icons" in issues[0].message


# --- NarrativeConsistency ---

def test_narrative_consistency_enough_panels() -> None:
    ev = get_evaluator("narrative_consistency")
    with tempfile.TemporaryDirectory() as d:
        comp_path = Path(d) / "final.png"
        _make_image(comp_path)
        scenario = ScenarioConfig(
            name="test",
            assets={"panel_count_range": [4, 8]},
        )
        panels = [
            _spec(f"panel_{i}").model_copy(update={"type": "panel"})
            for i in range(4)
        ]
        issues = ev.evaluate(
            scenario=scenario, specs=panels,
            generated_assets=[], composition=_composition(str(comp_path)),
        )
    assert issues == []


def test_narrative_consistency_too_few_panels() -> None:
    ev = get_evaluator("narrative_consistency")
    with tempfile.TemporaryDirectory() as d:
        comp_path = Path(d) / "final.png"
        _make_image(comp_path)
        scenario = ScenarioConfig(
            name="test",
            assets={"panel_count_range": [4, 8]},
        )
        panels = [
            _spec("panel_1").model_copy(update={"type": "panel"}),
        ]
        issues = ev.evaluate(
            scenario=scenario, specs=panels,
            generated_assets=[], composition=_composition(str(comp_path)),
        )
    assert len(issues) == 1
    assert issues[0].category == "narrative_coverage"
