"""Revision controller for agentic loops."""

from graphic_agent.schemas import CritiqueReport, RevisionDecision, ScenarioConfig


class RevisionController:
    """Choose whether to accept or retry after a critique round."""

    def decide(
        self,
        report: CritiqueReport,
        scenario: ScenarioConfig,
        round_index: int,
    ) -> RevisionDecision:
        if report.passed:
            return RevisionDecision(
                action="accept",
                rationale=(
                    f"Score {report.score} passed threshold {scenario.revision.quality_threshold}."
                ),
            )
        if round_index >= scenario.revision.max_rounds:
            return RevisionDecision(
                action="stop",
                rationale="Revision budget exhausted; returning best available result.",
            )
        retry_asset_ids = [issue.asset_id for issue in report.issues if issue.asset_id]
        return RevisionDecision(
            action="retry_assets",
            rationale="Retry assets referenced by the structured critique report.",
            retry_asset_ids=sorted(set(retry_asset_ids)),
        )
