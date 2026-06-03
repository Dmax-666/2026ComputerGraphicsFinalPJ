"""Tests for RevisionController prompt rewriting and reasoning."""

from graphic_agent.agents.revision import RevisionController
from graphic_agent.schemas import (
    AssetSpec,
    CritiqueIssue,
    CritiqueReport,
    ScenarioConfig,
)


def _spec(id: str, prompt: str = "original prompt") -> AssetSpec:
    return AssetSpec(
        id=id, type="visual", category="generic",
        title="T", description="D", purpose="P", prompt=prompt,
    )


def _report(score: float, issues: list[CritiqueIssue] | None = None) -> CritiqueReport:
    passed = score >= 0.75 and not any(
        i.severity == "high" for i in (issues or [])
    )
    return CritiqueReport(
        score=score, passed=passed,
        summary="test", issues=issues or [],
    )


def test_accept_when_passed() -> None:
    ctrl = RevisionController()
    scenario = ScenarioConfig(name="test", revision={"max_rounds": 3, "quality_threshold": 0.75})
    decision = ctrl.decide(_report(0.9), scenario, round_index=1)
    assert decision.action == "accept"
    assert len(decision.reasoning_trace) > 0


def test_stop_when_budget_exhausted() -> None:
    ctrl = RevisionController()
    scenario = ScenarioConfig(name="test", revision={"max_rounds": 2, "quality_threshold": 0.75})
    report = _report(0.5, [
        CritiqueIssue(asset_id="a1", severity="high", category="style",
                      message="bad", recommendation="fix it"),
    ])
    decision = ctrl.decide(report, scenario, round_index=2)
    assert decision.action == "stop"
    assert "exhausted" in decision.rationale.lower() or "budget" in decision.rationale.lower()


def test_retry_with_prompt_rewrites() -> None:
    ctrl = RevisionController()
    scenario = ScenarioConfig(name="test", revision={"max_rounds": 3, "quality_threshold": 0.75})
    specs = [_spec("a1", "draw a cat"), _spec("a2", "draw a dog")]
    report = _report(0.5, [
        CritiqueIssue(asset_id="a1", severity="high", category="style",
                      message="style drifted", recommendation="add style anchors"),
    ])
    decision = ctrl.decide(report, scenario, round_index=1, specs=specs)

    assert decision.action == "retry_assets"
    assert "a1" in decision.retry_asset_ids
    assert "a1" in decision.prompt_rewrites
    assert "add style anchors" in decision.prompt_rewrites["a1"]
    assert "a2" not in decision.prompt_rewrites  # no issue for a2
    assert len(decision.reasoning_trace) > 0


def test_multiple_issues_same_asset_accumulate_rewrites() -> None:
    ctrl = RevisionController()
    scenario = ScenarioConfig(name="test", revision={"max_rounds": 3, "quality_threshold": 0.75})
    specs = [_spec("a1", "original")]
    report = _report(0.3, [
        CritiqueIssue(asset_id="a1", severity="high", category="style",
                      message="wrong color", recommendation="use blue"),
        CritiqueIssue(asset_id="a1", severity="medium", category="layout",
                      message="too cluttered", recommendation="simplify background"),
    ])
    decision = ctrl.decide(report, scenario, round_index=1, specs=specs)

    assert "use blue" in decision.prompt_rewrites["a1"]
    assert "simplify background" in decision.prompt_rewrites["a1"]


def test_reasoning_trace_includes_all_issues() -> None:
    ctrl = RevisionController()
    scenario = ScenarioConfig(name="test", revision={"max_rounds": 3, "quality_threshold": 0.75})
    report = _report(0.4, [
        CritiqueIssue(asset_id="a1", severity="high", category="style",
                      message="msg1", recommendation="r1"),
        CritiqueIssue(asset_id="a2", severity="medium", category="layout",
                      message="msg2", recommendation="r2"),
    ])
    decision = ctrl.decide(report, scenario, round_index=1, specs=[_spec("a1"), _spec("a2")])

    trace_text = " ".join(decision.reasoning_trace)
    assert "msg1" in trace_text
    assert "msg2" in trace_text
