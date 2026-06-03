"""Narrative and character consistency evaluators."""

from __future__ import annotations

from graphic_agent.schemas import (
    AssetSpec,
    CompositionSpec,
    CritiqueIssue,
    GeneratedAsset,
    ScenarioConfig,
)


class NarrativeConsistencyEvaluator:
    """Check basic narrative structure: panel count within expected range."""

    name = "narrative_consistency"

    def evaluate(
        self,
        scenario: ScenarioConfig,
        specs: list[AssetSpec],
        generated_assets: list[GeneratedAsset],
        composition: CompositionSpec,
    ) -> list[CritiqueIssue]:
        panel_count = sum(1 for spec in specs if spec.type == "panel")
        panel_range = scenario.assets.get("panel_count_range")
        if not panel_range:
            return []
        min_panels = int(panel_range[0])
        if panel_count < min_panels:
            return [
                CritiqueIssue(
                    severity="medium",
                    category="narrative_coverage",
                    message=(
                        f"Comic has {panel_count} panels but scenario expects at least "
                        f"{min_panels}."
                    ),
                    recommendation="Add intermediate beats or increase requested panel count.",
                )
            ]
        return []


class CharacterConsistencyEvaluator:
    """Mock: placeholder for VLM-based cross-panel character identity check."""

    name = "character_consistency"

    def evaluate(
        self,
        scenario: ScenarioConfig,
        specs: list[AssetSpec],
        generated_assets: list[GeneratedAsset],
        composition: CompositionSpec,
    ) -> list[CritiqueIssue]:
        # Future: compare character embeddings across panels using VLM.
        return []
