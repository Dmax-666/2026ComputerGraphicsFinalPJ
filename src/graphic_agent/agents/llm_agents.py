"""LLM-backed agent implementations for real-provider runs."""

from __future__ import annotations

import base64
import json
import re
from pathlib import Path
from typing import Protocol

from graphic_agent.agents.critic import VisionCritic
from graphic_agent.agents.planner import Planner
from graphic_agent.agents.revision import RevisionController
from graphic_agent.agents.style_director import StyleDirector
from graphic_agent.schemas import (
    AssetSpec,
    CompositionSpec,
    CritiqueIssue,
    CritiqueReport,
    GeneratedAsset,
    ProviderUsage,
    RevisionDecision,
    ScenarioConfig,
    StyleGuide,
    VisualTask,
)


def _string_list(value, fallback: list[str]) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [str(item) for item in value]
    return fallback


def _normalize_severity(value) -> str:
    normalized = str(value or "low").strip().lower()
    if normalized in {"critical", "major", "severe", "blocker"}:
        return "high"
    if normalized in {"moderate", "mid"}:
        return "medium"
    if normalized in {"minor", "info", "informational"}:
        return "low"
    if normalized in {"low", "medium", "high"}:
        return normalized
    return "low"


class TextCompletionTool(Protocol):
    def complete(self, system_prompt: str, user_prompt: str) -> tuple[str, ProviderUsage]:
        """Return text content plus provider usage metadata."""

    def complete_messages(self, messages: list[dict]) -> tuple[str, ProviderUsage]:
        """Return text content for arbitrary chat messages, including image content."""


def _load_json_object(content: str) -> dict:
    try:
        payload = json.loads(content)
    except json.JSONDecodeError:
        fenced = re.search(r"```(?:json)?\s*(.*?)```", content, flags=re.DOTALL)
        if fenced:
            payload = json.loads(fenced.group(1))
        else:
            inline = re.search(r"\{.*\}", content, flags=re.DOTALL)
            if not inline:
                raise
            payload = json.loads(inline.group(0))
    if not isinstance(payload, dict):
        raise ValueError("LLM response must be a JSON object.")
    return payload


class LLMStyleDirector:
    """Create a richer StyleGuide with a text model, falling back to local rules."""

    def __init__(
        self,
        text_generator: TextCompletionTool,
        fallback: StyleDirector | None = None,
    ) -> None:
        self.text_generator = text_generator
        self.fallback = fallback or StyleDirector()
        self.last_report: dict = {}
        self.last_usage: list[ProviderUsage] = []

    def create_style_guide(self, task: VisualTask, scenario: ScenarioConfig) -> StyleGuide:
        baseline = self.fallback.create_style_guide(task, scenario)
        self.last_report = {
            "enabled": True,
            "stage": "style_director",
            "fallback_style_guide": baseline.model_dump(mode="json"),
        }
        self.last_usage = []
        system_prompt = (
            "You are the style director for a visual generation pipeline. Return strict JSON "
            "matching this schema: name, visual_style, palette, mood, typography, "
            "negative_prompt, notes. Keep values concise and useful for image generation."
        )
        user_prompt = json.dumps(
            {
                "scenario": scenario.model_dump(mode="json"),
                "task": task.model_dump(mode="json"),
                "baseline_style_guide": baseline.model_dump(mode="json"),
            },
            ensure_ascii=False,
        )
        try:
            content, usage = self.text_generator.complete(system_prompt, user_prompt)
            payload = _load_json_object(content)
            style_guide = StyleGuide(
                name=str(payload.get("name") or baseline.name),
                visual_style=str(payload.get("visual_style") or baseline.visual_style),
                palette=[str(value) for value in payload.get("palette", baseline.palette)],
                mood=str(payload.get("mood") or baseline.mood),
                typography=str(payload.get("typography") or baseline.typography),
                negative_prompt=str(
                    payload.get("negative_prompt") or baseline.negative_prompt
                ),
                notes=_string_list(payload.get("notes"), baseline.notes),
            )
            self.last_usage = [usage]
            self.last_report.update(
                {
                    "status": "llm_generated",
                    "provider_profile": usage.provider_profile,
                    "provider": usage.provider,
                    "model": usage.model,
                    "style_guide": style_guide.model_dump(mode="json"),
                }
            )
            return style_guide
        except Exception as exc:
            self.last_report.update({"status": "fallback", "reason": str(exc)})
            return baseline


class LLMPlanner:
    """Plan structured AssetSpec objects with a text model."""

    def __init__(
        self,
        text_generator: TextCompletionTool,
        fallback: Planner | None = None,
    ) -> None:
        self.text_generator = text_generator
        self.fallback = fallback or Planner()
        self.last_report: dict = {}
        self.last_usage: list[ProviderUsage] = []

    def plan(
        self,
        task: VisualTask,
        scenario: ScenarioConfig,
        style_guide: StyleGuide,
    ) -> list[AssetSpec]:
        baseline = self.fallback.plan(task, scenario, style_guide)
        self.last_report = {
            "enabled": True,
            "stage": "planner",
            "fallback_asset_count": len(baseline),
        }
        self.last_usage = []
        system_prompt = (
            "You are a visual planning agent. Return strict JSON with key 'assets'. "
            "Each asset must include id, type, category, title, description, purpose, "
            "prompt, order, size, depends_on, and metadata. Preserve the scenario's target "
            "asset count unless the task explicitly requires fewer."
        )
        user_prompt = json.dumps(
            {
                "scenario": scenario.model_dump(mode="json"),
                "task": task.model_dump(mode="json"),
                "style_guide": style_guide.model_dump(mode="json"),
                "baseline_assets": [spec.model_dump(mode="json") for spec in baseline],
            },
            ensure_ascii=False,
        )
        try:
            content, usage = self.text_generator.complete(system_prompt, user_prompt)
            payload = _load_json_object(content)
            raw_assets = payload.get("assets")
            if not isinstance(raw_assets, list) or not raw_assets:
                raise ValueError("LLM planner response did not include assets.")
            specs = [AssetSpec.model_validate(item) for item in raw_assets]
            self._validate_specs(specs)
            self.last_usage = [usage]
            self.last_report.update(
                {
                    "status": "llm_generated",
                    "provider_profile": usage.provider_profile,
                    "provider": usage.provider,
                    "model": usage.model,
                    "asset_count": len(specs),
                }
            )
            return specs
        except Exception as exc:
            self.last_report.update({"status": "fallback", "reason": str(exc)})
            return baseline

    def _validate_specs(self, specs: list[AssetSpec]) -> None:
        ids = [spec.id for spec in specs]
        if len(ids) != len(set(ids)):
            raise ValueError("LLM planner returned duplicate asset ids.")
        for spec in specs:
            if spec.order < 0:
                raise ValueError(f"Asset '{spec.id}' has invalid order.")


class LLMCritic:
    """Review final output with local evaluators plus optional VLM judgment."""

    def __init__(
        self,
        text_generator: TextCompletionTool,
        fallback: VisionCritic | None = None,
    ) -> None:
        self.text_generator = text_generator
        self.fallback = fallback or VisionCritic()
        self.last_report: dict = {}
        self.last_usage: list[ProviderUsage] = []

    def review(
        self,
        scenario: ScenarioConfig,
        specs: list[AssetSpec],
        generated_assets: list[GeneratedAsset],
        composition: CompositionSpec,
    ) -> CritiqueReport:
        local_report = self.fallback.review(scenario, specs, generated_assets, composition)
        self.last_report = {
            "enabled": True,
            "stage": "critic",
            "local_report": local_report.model_dump(mode="json"),
        }
        self.last_usage = []
        try:
            return self._review_with_llm(
                scenario,
                local_report,
                self._build_review_messages(
                    scenario,
                    specs,
                    generated_assets,
                    composition,
                    local_report,
                    include_image=True,
                ),
                status="llm_vision_reviewed",
            )
        except Exception as vision_exc:
            self.last_report["vision_error"] = str(vision_exc)
            try:
                return self._review_with_llm(
                    scenario,
                    local_report,
                    self._build_review_messages(
                        scenario,
                        specs,
                        generated_assets,
                        composition,
                        local_report,
                        include_image=False,
                    ),
                    status="llm_text_reviewed",
                )
            except Exception as text_exc:
                self.last_report.update({"status": "fallback", "reason": str(text_exc)})
                return local_report

    def _review_with_llm(
        self,
        scenario: ScenarioConfig,
        local_report: CritiqueReport,
        messages: list[dict],
        *,
        status: str,
    ) -> CritiqueReport:
        content, usage = self.text_generator.complete_messages(messages)
        payload = _load_json_object(content)
        llm_issues = [
            CritiqueIssue.model_validate(
                {
                    **item,
                    "severity": _normalize_severity(item.get("severity")),
                }
            )
            for item in payload.get("issues", [])
            if isinstance(item, dict)
        ]
        llm_score = float(payload.get("score", local_report.score))
        merged_issues = local_report.issues + llm_issues
        score = min(local_report.score, max(0.0, min(1.0, round(llm_score, 3))))
        passed = score >= scenario.revision.quality_threshold and not any(
            issue.severity == "high" for issue in merged_issues
        )
        summary = str(payload.get("summary") or local_report.summary)
        evaluator_name = (
            "llm_vision_critic" if status == "llm_vision_reviewed" else "llm_text_critic"
        )
        self.last_usage = [usage]
        self.last_report.update(
            {
                "status": status,
                "provider_profile": usage.provider_profile,
                "provider": usage.provider,
                "model": usage.model,
                "llm_score": llm_score,
                "llm_issue_count": len(llm_issues),
            }
        )
        return CritiqueReport(
            score=score,
            passed=passed,
            summary=summary,
            issues=merged_issues,
            evaluator_names=list(
                dict.fromkeys(local_report.evaluator_names + [evaluator_name])
            ),
        )

    def _build_review_messages(
        self,
        scenario: ScenarioConfig,
        specs: list[AssetSpec],
        generated_assets: list[GeneratedAsset],
        composition: CompositionSpec,
        local_report: CritiqueReport,
        *,
        include_image: bool,
    ) -> list[dict]:
        prompt = json.dumps(
            {
                "instructions": (
                    "Review the final composition for task fit, story coherence, asset "
                    "consistency, visual defects, and whether any asset should be retried. "
                    "Return strict JSON with score, passed, summary, and issues. Each issue "
                    "must include asset_id, severity, category, message, recommendation."
                ),
                "scenario": scenario.model_dump(mode="json"),
                "assets": [spec.model_dump(mode="json") for spec in specs],
                "generated_assets": [
                    {
                        "spec_id": asset.spec_id,
                        "path": asset.path,
                        "metadata": asset.metadata,
                    }
                    for asset in generated_assets
                ],
                "composition": composition.model_dump(mode="json"),
                "local_report": local_report.model_dump(mode="json"),
            },
            ensure_ascii=False,
        )
        image_path = Path(composition.output_path)
        if not include_image or not image_path.exists():
            return [
                {
                    "role": "system",
                    "content": "You are a strict visual critic. Return JSON only.",
                },
                {"role": "user", "content": prompt},
            ]
        image_data = base64.b64encode(image_path.read_bytes()).decode("ascii")
        return [
            {
                "role": "system",
                "content": "You are a strict visual critic. Return JSON only.",
            },
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/png;base64,{image_data}"},
                    },
                ],
            },
        ]


class LLMRevisionController:
    """Use a text model to decide accept/retry and rewrite failed prompts."""

    def __init__(
        self,
        text_generator: TextCompletionTool,
        fallback: RevisionController | None = None,
    ) -> None:
        self.text_generator = text_generator
        self.fallback = fallback or RevisionController()
        self.last_report: dict = {}
        self.last_usage: list[ProviderUsage] = []

    def decide(
        self,
        report: CritiqueReport,
        scenario: ScenarioConfig,
        round_index: int,
        specs: list[AssetSpec] | None = None,
    ) -> RevisionDecision:
        fallback_decision = self.fallback.decide(report, scenario, round_index, specs)
        specs = specs or []
        self.last_report = {
            "enabled": True,
            "stage": "revision_controller",
            "fallback_decision": fallback_decision.model_dump(mode="json"),
        }
        self.last_usage = []
        system_prompt = (
            "You are a revision controller for an image-generation pipeline. Return strict "
            "JSON with action, rationale, retry_asset_ids, prompt_rewrites, reasoning_trace. "
            "action must be one of accept, retry_assets, stop. Respect the revision budget."
        )
        user_prompt = json.dumps(
            {
                "scenario": scenario.model_dump(mode="json"),
                "round_index": round_index,
                "critique_report": report.model_dump(mode="json"),
                "assets": [spec.model_dump(mode="json") for spec in specs],
                "fallback_decision": fallback_decision.model_dump(mode="json"),
            },
            ensure_ascii=False,
        )
        try:
            content, usage = self.text_generator.complete(system_prompt, user_prompt)
            payload = _load_json_object(content)
            decision = RevisionDecision.model_validate(payload)
            valid_ids = {spec.id for spec in specs}
            decision.retry_asset_ids = [
                asset_id for asset_id in decision.retry_asset_ids if asset_id in valid_ids
            ]
            decision.prompt_rewrites = {
                asset_id: prompt
                for asset_id, prompt in decision.prompt_rewrites.items()
                if asset_id in valid_ids and prompt
            }
            if report.passed and decision.action != "accept":
                decision = fallback_decision
            if (
                round_index >= scenario.revision.max_rounds
                and decision.action == "retry_assets"
            ):
                decision = fallback_decision
            if decision.action == "retry_assets" and not decision.retry_asset_ids:
                decision = fallback_decision
            self.last_usage = [usage]
            self.last_report.update(
                {
                    "status": "llm_decided",
                    "provider_profile": usage.provider_profile,
                    "provider": usage.provider,
                    "model": usage.model,
                    "decision": decision.model_dump(mode="json"),
                }
            )
            return decision
        except Exception as exc:
            self.last_report.update({"status": "fallback", "reason": str(exc)})
            return fallback_decision
