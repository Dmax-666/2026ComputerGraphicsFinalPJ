"""Layout quality evaluators."""

from __future__ import annotations

from graphic_agent.schemas import (
    AssetSpec,
    CompositionSpec,
    CritiqueIssue,
    GeneratedAsset,
    ScenarioConfig,
)


def area(box: tuple[int, int, int, int]) -> int:
    left, top, right, bottom = box
    return max(0, right - left) * max(0, bottom - top)


class TextLayoutQualityEvaluator:
    """Mock: placeholder for checking text overlap, readability, bubble
    placement, etc."""

    name = "text_layout_quality"

    def evaluate(
        self,
        scenario: ScenarioConfig,
        specs: list[AssetSpec],
        generated_assets: list[GeneratedAsset],
        composition: CompositionSpec,
    ) -> list[CritiqueIssue]:
        # Future: use OCR or VLM to detect text overlap / illegible regions.
        return []
