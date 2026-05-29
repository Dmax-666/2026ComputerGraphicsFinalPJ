"""Mock visual critic and quality gate."""

from pathlib import Path

from graphic_agent.schemas import (
    AssetSpec,
    CompositionSpec,
    CritiqueIssue,
    CritiqueReport,
    GeneratedAsset,
    ScenarioConfig,
)


class VisionCritic:
    """Check generated outputs against scenario-level quality expectations."""

    def review(
        self,
        scenario: ScenarioConfig,
        specs: list[AssetSpec],
        generated_assets: list[GeneratedAsset],
        composition: CompositionSpec,
    ) -> CritiqueReport:
        issues: list[CritiqueIssue] = []
        generated_by_id = {asset.spec_id: asset for asset in generated_assets}

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
                continue
            if not Path(asset.path).exists():
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

        if scenario.name == "story_comic":
            panel_count = sum(1 for spec in specs if spec.type == "panel")
            min_panels = int(scenario.assets.get("panel_count_range", [4, 8])[0])
            if panel_count < min_panels:
                issues.append(
                    CritiqueIssue(
                        severity="medium",
                        category="narrative_coverage",
                        message="Comic has fewer panels than the scenario expects.",
                        recommendation="Add intermediate beats or increase requested panel count.",
                    )
                )

        if scenario.name == "game_assets":
            expected_categories = set(scenario.assets.get("categories", []))
            present_categories = {spec.category for spec in specs}
            missing_categories = sorted(expected_categories - present_categories)
            if missing_categories:
                issues.append(
                    CritiqueIssue(
                        severity="medium",
                        category="category_coverage",
                        message=f"Missing categories: {', '.join(missing_categories)}",
                        recommendation="Plan at least one asset for each configured category.",
                    )
                )

        penalty = sum(0.25 if issue.severity == "high" else 0.1 for issue in issues)
        score = max(0.0, round(1.0 - penalty, 3))
        passed = score >= scenario.revision.quality_threshold and not any(
            issue.severity == "high" for issue in issues
        )
        summary = "Accepted by mock critic." if passed else "Issues found by mock critic."
        return CritiqueReport(
            score=score,
            passed=passed,
            summary=summary,
            issues=issues,
            evaluator_names=scenario.evaluators,
        )
