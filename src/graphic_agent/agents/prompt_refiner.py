"""Prompt refinement agent for real-provider image runs."""

from __future__ import annotations

import json
import re
from typing import Protocol

from graphic_agent.schemas import (
    AssetSpec,
    ProviderUsage,
    ScenarioConfig,
    StyleGuide,
    VisualTask,
)


class TextCompletionTool(Protocol):
    def complete(self, system_prompt: str, user_prompt: str) -> tuple[str, ProviderUsage]:
        """Return text content plus provider usage metadata."""


class NoOpPromptRefiner:
    """Keep deterministic mock and offline runs unchanged."""

    def refine(
        self,
        *,
        task: VisualTask,
        scenario: ScenarioConfig,
        style_guide: StyleGuide,
        specs: list[AssetSpec],
    ) -> tuple[list[AssetSpec], dict, list[ProviderUsage]]:
        return specs, {"enabled": False, "reason": "No text provider configured."}, []


class LLMPromptRefiner:
    """Use a text model to rewrite image prompts before calling the image API."""

    def __init__(self, text_generator: TextCompletionTool) -> None:
        self.text_generator = text_generator

    def refine(
        self,
        *,
        task: VisualTask,
        scenario: ScenarioConfig,
        style_guide: StyleGuide,
        specs: list[AssetSpec],
    ) -> tuple[list[AssetSpec], dict, list[ProviderUsage]]:
        if not specs:
            return specs, {"enabled": True, "assets": []}, []

        system_prompt = (
            "You rewrite image-generation prompts for a visual generation pipeline. "
            "Return strict JSON only. Preserve each asset id and improve prompts for "
            "clear visual composition, style consistency, and generation reliability. "
            "Do not add unsafe content. Do not change asset sizes."
        )
        user_prompt = json.dumps(
            {
                "scenario": scenario.name,
                "task": task.model_dump(mode="json"),
                "style_guide": style_guide.model_dump(mode="json"),
                "assets": [
                    {
                        "id": spec.id,
                        "type": spec.type,
                        "category": spec.category,
                        "title": spec.title,
                        "description": spec.description,
                        "purpose": spec.purpose,
                        "size": list(spec.size),
                        "prompt": spec.prompt,
                        "metadata": spec.metadata,
                    }
                    for spec in specs
                ],
                "output_schema": {
                    "assets": [
                        {
                            "id": "same asset id",
                            "prompt": "rewritten image-generation prompt",
                        }
                    ]
                },
            },
            ensure_ascii=False,
        )
        content, usage = self.text_generator.complete(system_prompt, user_prompt)
        prompt_by_id = self._parse_prompt_map(content)
        refined_specs: list[AssetSpec] = []
        report_assets: list[dict[str, str]] = []

        for spec in specs:
            refined_prompt = prompt_by_id.get(spec.id)
            if not refined_prompt:
                refined_specs.append(spec)
                report_assets.append(
                    {
                        "id": spec.id,
                        "status": "unchanged",
                        "original_prompt": spec.prompt,
                        "refined_prompt": spec.prompt,
                    }
                )
                continue
            refined_specs.append(
                spec.model_copy(
                    update={
                        "prompt": refined_prompt,
                        "metadata": {
                            **spec.metadata,
                            "original_prompt": spec.prompt,
                            "prompt_refined_by": usage.model,
                        },
                    }
                )
            )
            report_assets.append(
                {
                    "id": spec.id,
                    "status": "refined",
                    "original_prompt": spec.prompt,
                    "refined_prompt": refined_prompt,
                }
            )

        return (
            refined_specs,
            {
                "enabled": True,
                "provider_profile": usage.provider_profile,
                "provider": usage.provider,
                "model": usage.model,
                "assets": report_assets,
            },
            [usage],
        )

    def _parse_prompt_map(self, content: str) -> dict[str, str]:
        payload = self._load_json(content)
        assets = payload.get("assets") if isinstance(payload, dict) else None
        if not isinstance(assets, list):
            return {}
        prompt_by_id: dict[str, str] = {}
        for item in assets:
            if not isinstance(item, dict):
                continue
            asset_id = item.get("id")
            prompt = item.get("prompt")
            if isinstance(asset_id, str) and isinstance(prompt, str) and prompt.strip():
                prompt_by_id[asset_id] = prompt.strip()
        return prompt_by_id

    def _load_json(self, content: str) -> dict:
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            match = re.search(r"```(?:json)?\s*(.*?)```", content, flags=re.DOTALL)
            if match:
                return json.loads(match.group(1))
            match = re.search(r"\{.*\}", content, flags=re.DOTALL)
            if match:
                return json.loads(match.group(0))
            raise
