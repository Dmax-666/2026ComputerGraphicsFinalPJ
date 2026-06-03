"""Evaluator protocol and registry.

Scenario YAML declares ``evaluators: [name, ...]``. The critic resolves each
name through this registry, calls ``evaluate()``, and merges the resulting
issues into the final ``CritiqueReport``.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from graphic_agent.schemas import (
    AssetSpec,
    CompositionSpec,
    CritiqueIssue,
    GeneratedAsset,
    ScenarioConfig,
)


@runtime_checkable
class Evaluator(Protocol):
    """Contract every pluggable evaluator must satisfy."""

    name: str

    def evaluate(
        self,
        scenario: ScenarioConfig,
        specs: list[AssetSpec],
        generated_assets: list[GeneratedAsset],
        composition: CompositionSpec,
    ) -> list[CritiqueIssue]: ...


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

_REGISTRY: dict[str, type[Evaluator]] = {}


def register_evaluator(name: str, cls: type[Evaluator]) -> None:
    _REGISTRY[name] = cls


def get_evaluator(name: str) -> Evaluator:
    try:
        return _REGISTRY[name]()
    except KeyError as exc:
        available = ", ".join(sorted(_REGISTRY)) or "(none)"
        raise ValueError(
            f"Unknown evaluator '{name}'. Available: {available}"
        ) from exc


def list_evaluators() -> list[str]:
    return sorted(_REGISTRY)


# ---------------------------------------------------------------------------
# Auto-register built-in evaluators on import
# ---------------------------------------------------------------------------

def _auto_register() -> None:
    from graphic_agent.evaluators.asset_completeness import AssetCompletenessEvaluator
    from graphic_agent.evaluators.consistency import (
        CategoryCoverageEvaluator,
        StyleConsistencyEvaluator,
    )
    from graphic_agent.evaluators.image_sanity import FileSanityEvaluator, ImageSizeEvaluator
    from graphic_agent.evaluators.layout_quality import TextLayoutQualityEvaluator
    from graphic_agent.evaluators.narrative import (
        CharacterConsistencyEvaluator,
        NarrativeConsistencyEvaluator,
    )

    register_evaluator("style_consistency", StyleConsistencyEvaluator)
    register_evaluator("category_coverage", CategoryCoverageEvaluator)
    register_evaluator("text_layout_quality", TextLayoutQualityEvaluator)
    register_evaluator("narrative_consistency", NarrativeConsistencyEvaluator)
    register_evaluator("character_consistency", CharacterConsistencyEvaluator)
    register_evaluator("asset_completeness", AssetCompletenessEvaluator)
    register_evaluator("image_size", ImageSizeEvaluator)
    register_evaluator("file_sanity", FileSanityEvaluator)


_auto_register()
