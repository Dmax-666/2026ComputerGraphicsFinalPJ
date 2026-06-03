"""Config-driven visual generation pipeline."""

from pathlib import Path

from graphic_agent.agents.critic import VisionCritic
from graphic_agent.agents.planner import Planner
from graphic_agent.agents.revision import RevisionController
from graphic_agent.agents.style_director import StyleDirector
from graphic_agent.costing import record_generated_assets
from graphic_agent.registry import get_renderer
from graphic_agent.schemas import (
    AssetSpec,
    ContextMemory,
    CostSummary,
    GeneratedAsset,
    PipelineResult,
    ScenarioConfig,
    VisualTask,
)
from graphic_agent.tools.image_gen import MockImageGenerator
from graphic_agent.tools.storage import RunStorage


class GraphicAgentPipeline:
    """Run one scenario with one task input."""

    def __init__(self, scenario: ScenarioConfig, output_dir: Path | str) -> None:
        self.scenario = scenario
        self.storage = RunStorage(output_dir)
        self.style_director = StyleDirector()
        self.planner = Planner()
        self.image_generator = MockImageGenerator()
        self.critic = VisionCritic()
        self.revision_controller = RevisionController()
        self.renderer = get_renderer(scenario.render.type)

    def run(self, task: VisualTask) -> PipelineResult:
        self.storage.prepare()
        self.storage.write_json("reports/task.json", task)

        style_guide = self.style_director.create_style_guide(task, self.scenario)
        specs = self.planner.plan(task, self.scenario, style_guide)
        self.storage.write_json("reports/style_guide.json", style_guide)
        self.storage.write_json(
            "reports/plan.json",
            {"assets": [spec.model_dump(mode="json") for spec in specs]},
        )

        context_memory = ContextMemory()
        cost_summary = CostSummary()
        generated_assets = self._generate_all(specs, style_guide, round_index=1)
        record_generated_assets(cost_summary, generated_assets, is_retry=False)

        # Populate reference image paths into context memory after initial generation.
        for asset in generated_assets:
            spec = next((s for s in specs if s.id == asset.spec_id), None)
            if spec and spec.type == "character_reference":
                role = spec.metadata.get("role", spec.id)
                context_memory.reference_image_paths[role] = asset.path
                style_guide.reference_assets[role] = asset.path

        final_composition = None
        final_report = None
        final_decision = None
        rounds_completed = 0

        for round_index in range(1, self.scenario.revision.max_rounds + 1):
            rounds_completed = round_index
            final_composition = self.renderer.render(
                task=task,
                specs=specs,
                generated_assets=generated_assets,
                config=self.scenario.render,
                output_dir=self.storage.output_dir,
            )
            final_report = self.critic.review(
                scenario=self.scenario,
                specs=specs,
                generated_assets=generated_assets,
                composition=final_composition,
            )
            final_decision = self.revision_controller.decide(
                final_report,
                self.scenario,
                round_index=round_index,
                specs=specs,
            )
            self.storage.write_json(f"reports/critique_round_{round_index}.json", final_report)
            self.storage.write_json(f"reports/revision_round_{round_index}.json", final_decision)

            # Accumulate revision lessons into context memory.
            for issue in final_report.issues:
                context_memory.revision_lessons.append(
                    f"Round {round_index}: [{issue.severity}] {issue.category} - "
                    f"{issue.recommendation}"
                )
            if final_decision.action != "retry_assets":
                break
            retry_ids = set(final_decision.retry_asset_ids)
            if not retry_ids:
                break
            retry_specs = self._apply_prompt_rewrites(
                [spec for spec in specs if spec.id in retry_ids],
                final_decision.prompt_rewrites,
            )
            regenerated = self._generate_all(
                retry_specs,
                style_guide,
                round_index=round_index + 1,
            )
            record_generated_assets(cost_summary, regenerated, is_retry=True)
            generated_assets = self._replace_assets(generated_assets, regenerated)

        if final_composition is None or final_report is None or final_decision is None:
            raise RuntimeError("Pipeline ended before producing a composition and critique report.")

        cost_summary.total_rounds = rounds_completed
        self.storage.write_json("reports/context_memory.json", context_memory)
        self.storage.write_json("reports/cost_summary.json", cost_summary)

        result = PipelineResult(
            scenario=self.scenario.name,
            task=task,
            style_guide=style_guide,
            context_memory=context_memory,
            cost_summary=cost_summary,
            planned_assets=specs,
            generated_assets=generated_assets,
            composition=final_composition,
            critique=final_report,
            revision=final_decision,
            output_dir=str(self.storage.output_dir),
            final_image=final_composition.output_path,
            rounds_completed=rounds_completed,
        )
        self.storage.write_json("reports/result.json", result)
        return result

    def _generate_all(
        self,
        specs: list[AssetSpec],
        style_guide,
        round_index: int,
    ) -> list[GeneratedAsset]:
        return [
            self.image_generator.generate(spec, style_guide, self.storage.assets_dir, round_index)
            for spec in specs
        ]

    @staticmethod
    def _apply_prompt_rewrites(
        specs: list[AssetSpec],
        rewrites: dict[str, str],
    ) -> list[AssetSpec]:
        """Return copies of specs with prompts replaced by critique-informed rewrites."""
        if not rewrites:
            return specs
        result: list[AssetSpec] = []
        for spec in specs:
            if spec.id in rewrites:
                result.append(spec.model_copy(update={"prompt": rewrites[spec.id]}))
            else:
                result.append(spec)
        return result

    def _replace_assets(
        self,
        existing: list[GeneratedAsset],
        regenerated: list[GeneratedAsset],
    ) -> list[GeneratedAsset]:
        regenerated_by_id = {asset.spec_id: asset for asset in regenerated}
        merged = [regenerated_by_id.get(asset.spec_id, asset) for asset in existing]
        existing_ids = {asset.spec_id for asset in existing}
        merged.extend(asset for asset in regenerated if asset.spec_id not in existing_ids)
        return merged
