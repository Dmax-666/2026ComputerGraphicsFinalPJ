"""Composable visual critic that delegates to registered evaluators."""

from graphic_agent.evaluators.registry import get_evaluator
from graphic_agent.schemas import (
    AssetSpec,
    CompositionSpec,
    CritiqueIssue,
    CritiqueReport,
    GeneratedAsset,
    ScenarioConfig,
)


class VisionCritic:
    """Check generated outputs by running every evaluator declared in the
    scenario config.

    The critic itself contains no scenario-specific logic — all quality rules
    live in evaluator modules resolved through the evaluator registry.
    """

    def review(
        self,
        scenario: ScenarioConfig,
        specs: list[AssetSpec],
        generated_assets: list[GeneratedAsset],
        composition: CompositionSpec,
    ) -> CritiqueReport:
        issues: list[CritiqueIssue] = []
        evaluator_names: list[str] = []

        # Always run asset completeness as a baseline check.
        baseline_evaluators = ["asset_completeness"]
        all_evaluator_names = list(dict.fromkeys(baseline_evaluators + scenario.evaluators))

        for name in all_evaluator_names:
            evaluator = get_evaluator(name)
            evaluator_names.append(name)
            issues.extend(
                evaluator.evaluate(
                    scenario=scenario,
                    specs=specs,
                    generated_assets=generated_assets,
                    composition=composition,
                )
            )

        penalty = sum(0.25 if issue.severity == "high" else 0.1 for issue in issues)
        score = max(0.0, round(1.0 - penalty, 3))
        passed = score >= scenario.revision.quality_threshold and not any(
            issue.severity == "high" for issue in issues
        )
        summary = "All evaluators passed." if passed else "Issues found during evaluation."

        return CritiqueReport(
            score=score,
            passed=passed,
            summary=summary,
            issues=issues,
            evaluator_names=evaluator_names,
        )
