"""Revision controller for agentic loops."""

from graphic_agent.schemas import (
    AssetSpec,
    CritiqueReport,
    RevisionDecision,
    ScenarioConfig,
)


class RevisionController:
    """Choose whether to accept or retry after a critique round.

    When retrying, the controller also produces prompt rewrites by appending
    critique recommendations to the original prompt.  Future LLM-backed
    controllers can do true prompt rewriting instead of concatenation.
    """

    def decide(
        self,
        report: CritiqueReport,
        scenario: ScenarioConfig,
        round_index: int,
        specs: list[AssetSpec] | None = None,
    ) -> RevisionDecision:
        if report.passed:
            return RevisionDecision(
                action="accept",
                rationale=(
                    f"Score {report.score} passed threshold "
                    f"{scenario.revision.quality_threshold}."
                ),
                reasoning_trace=[
                    f"Score {report.score} >= threshold {scenario.revision.quality_threshold}.",
                    "No high-severity issues found.",
                    "Accepting result.",
                ],
            )

        if round_index >= scenario.revision.max_rounds:
            return RevisionDecision(
                action="stop",
                rationale="Revision budget exhausted; returning best available result.",
                reasoning_trace=[
                    f"Round {round_index} >= max_rounds {scenario.revision.max_rounds}.",
                    f"Score {report.score} did not reach threshold.",
                    "Budget exhausted, stopping.",
                ],
            )

        retry_asset_ids = sorted(
            {issue.asset_id for issue in report.issues if issue.asset_id}
        )
        prompt_rewrites = self._build_prompt_rewrites(report, specs or [])
        reasoning_trace = self._build_reasoning_trace(report, retry_asset_ids)

        return RevisionDecision(
            action="retry_assets",
            rationale="Retry assets with prompt rewrites based on critique feedback.",
            retry_asset_ids=retry_asset_ids,
            prompt_rewrites=prompt_rewrites,
            reasoning_trace=reasoning_trace,
        )

    def _build_prompt_rewrites(
        self,
        report: CritiqueReport,
        specs: list[AssetSpec],
    ) -> dict[str, str]:
        """Append critique recommendations to original prompts.

        MVP strategy: concatenate.  LLM-backed controller should replace this
        with genuine prompt rewriting informed by the full critique context.
        """
        specs_by_id = {spec.id: spec for spec in specs}
        rewrites: dict[str, str] = {}

        for issue in report.issues:
            if not issue.asset_id or issue.asset_id not in specs_by_id:
                continue
            original = specs_by_id[issue.asset_id].prompt
            # If we already started rewriting this asset, build on top.
            base = rewrites.get(issue.asset_id, original)
            rewrites[issue.asset_id] = (
                f"{base} [Revision note: {issue.recommendation}]"
            )

        return rewrites

    def _build_reasoning_trace(
        self,
        report: CritiqueReport,
        retry_asset_ids: list[str],
    ) -> list[str]:
        trace = [f"Score {report.score} below threshold. {len(report.issues)} issue(s) found."]
        for issue in report.issues:
            target = f"asset '{issue.asset_id}'" if issue.asset_id else "composition"
            trace.append(f"[{issue.severity}] {target}: {issue.message}")
        trace.append(f"Retrying assets: {retry_asset_ids}")
        return trace
