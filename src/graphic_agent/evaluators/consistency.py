"""Style and category consistency evaluators."""

from __future__ import annotations

from graphic_agent.schemas import (
    AssetSpec,
    CompositionSpec,
    CritiqueIssue,
    GeneratedAsset,
    ScenarioConfig,
)


class StyleConsistencyEvaluator:
    """Mock: checks that all assets share the same provider (placeholder for
    future VLM-based style similarity scoring)."""

    name = "style_consistency"

    def evaluate(
        self,
        scenario: ScenarioConfig,
        specs: list[AssetSpec],
        generated_assets: list[GeneratedAsset],
        composition: CompositionSpec,
    ) -> list[CritiqueIssue]:
        # Future: use VLM embeddings to measure pairwise style distance.
        return []


class CategoryCoverageEvaluator:
    """Check that every category declared in the scenario has at least one
    planned asset."""

    name = "category_coverage"

    def evaluate(
        self,
        scenario: ScenarioConfig,
        specs: list[AssetSpec],
        generated_assets: list[GeneratedAsset],
        composition: CompositionSpec,
    ) -> list[CritiqueIssue]:
        expected = set(scenario.assets.get("categories", []))
        if not expected:
            return []
        present = {spec.category for spec in specs}
        missing = sorted(expected - present)
        if missing:
            return [
                CritiqueIssue(
                    severity="medium",
                    category="category_coverage",
                    message=f"Missing categories: {', '.join(missing)}",
                    recommendation="Plan at least one asset for each configured category.",
                )
            ]
        return []
