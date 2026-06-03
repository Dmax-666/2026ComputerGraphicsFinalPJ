"""Asset completeness evaluator."""

from __future__ import annotations

from pathlib import Path

from graphic_agent.schemas import (
    AssetSpec,
    CompositionSpec,
    CritiqueIssue,
    GeneratedAsset,
    ScenarioConfig,
)


class AssetCompletenessEvaluator:
    """Check that every planned asset was generated and its file exists."""

    name = "asset_completeness"

    def evaluate(
        self,
        scenario: ScenarioConfig,
        specs: list[AssetSpec],
        generated_assets: list[GeneratedAsset],
        composition: CompositionSpec,
    ) -> list[CritiqueIssue]:
        issues: list[CritiqueIssue] = []
        generated_by_id = {a.spec_id: a for a in generated_assets}

        for spec in specs:
            asset = generated_by_id.get(spec.id)
            if asset is None:
                issues.append(
                    CritiqueIssue(
                        asset_id=spec.id,
                        severity="high",
                        category="missing_asset",
                        message=f"Planned asset '{spec.id}' was not generated.",
                        recommendation="Regenerate this asset before final composition.",
                    )
                )
            elif not Path(asset.path).exists():
                issues.append(
                    CritiqueIssue(
                        asset_id=spec.id,
                        severity="high",
                        category="missing_file",
                        message=f"Generated file does not exist: {asset.path}",
                        recommendation="Check the image generator output path and retry.",
                    )
                )

        if not Path(composition.output_path).exists():
            issues.append(
                CritiqueIssue(
                    severity="high",
                    category="missing_composition",
                    message="Final composition image was not written.",
                    recommendation="Rerun renderer before accepting the result.",
                )
            )

        return issues
