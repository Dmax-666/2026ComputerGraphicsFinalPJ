"""Pre-run API budget estimation."""

from graphic_agent.schemas import (
    CostSummary,
    GeneratedAsset,
    ProviderFailure,
    ProviderProfile,
    ProviderUsage,
    RunBudgetEstimate,
    ScenarioConfig,
    SuiteBudgetEstimate,
)


def estimate_run_budget(
    scenario: ScenarioConfig,
    provider_profile: ProviderProfile,
    planned_asset_count: int,
) -> RunBudgetEstimate:
    """Estimate API spend before any external provider calls are made."""

    assumptions = provider_profile.pricing.get("assumptions", {})
    planner_cost = float(assumptions.get("planner_call_usd", 0))
    critic_cost = float(assumptions.get("critic_call_usd", 0))
    image_unit_cost = float(assumptions.get("image_generation_usd", 0))
    image_generation_cost = planned_asset_count * image_unit_cost

    retry_asset_count = planned_asset_count * scenario.revision.retry_budget_per_asset
    retry_buffer_cost = retry_asset_count * image_unit_cost
    baseline_total = planner_cost + critic_cost + image_generation_cost

    return RunBudgetEstimate(
        provider_profile=provider_profile.name,
        planned_asset_count=planned_asset_count,
        retry_buffer_asset_count=retry_asset_count,
        components={
            "planner_usd": round(planner_cost, 6),
            "critic_usd": round(critic_cost, 6),
            "image_generation_usd": round(image_generation_cost, 6),
            "retry_buffer_usd": round(retry_buffer_cost, 6),
        },
        baseline_total_usd=round(baseline_total, 6),
        with_retry_buffer_usd=round(baseline_total + retry_buffer_cost, 6),
    )


def combine_suite_estimates(
    suite_name: str,
    provider_profile: ProviderProfile,
    task_estimates: list[tuple[str, RunBudgetEstimate]],
) -> SuiteBudgetEstimate:
    """Combine per-task budget estimates into one suite estimate."""

    task_rows = [
        {
            "name": task_name,
            "planned_assets": estimate.planned_asset_count,
            "retry_buffer_assets": estimate.retry_buffer_asset_count,
            "baseline_total_usd": estimate.baseline_total_usd,
            "with_retry_buffer_usd": estimate.with_retry_buffer_usd,
        }
        for task_name, estimate in task_estimates
    ]
    return SuiteBudgetEstimate(
        suite_name=suite_name,
        provider_profile=provider_profile.name,
        task_estimates=task_rows,
        total_planned_assets=sum(row["planned_assets"] for row in task_rows),
        total_retry_buffer_assets=sum(row["retry_buffer_assets"] for row in task_rows),
        baseline_total_usd=round(sum(row["baseline_total_usd"] for row in task_rows), 6),
        with_retry_buffer_usd=round(
            sum(row["with_retry_buffer_usd"] for row in task_rows),
            6,
        ),
    )


def record_provider_usage(cost_summary: CostSummary, usage: ProviderUsage) -> CostSummary:
    """Merge one provider usage record into a run cost summary."""

    cost_summary.total_prompt_tokens += usage.prompt_tokens
    cost_summary.total_completion_tokens += usage.completion_tokens
    cost_summary.total_image_generations += usage.image_generations
    cost_summary.total_vision_calls += usage.vision_calls
    cost_summary.estimated_cost_usd = round(
        cost_summary.estimated_cost_usd + usage.estimated_cost_usd,
        6,
    )
    cost_summary.provider_usage.append(usage)
    return cost_summary


def record_provider_failure(
    cost_summary: CostSummary,
    failure: ProviderFailure,
) -> CostSummary:
    """Merge one structured provider failure into a run cost summary."""

    cost_summary.provider_failures.append(failure)
    return cost_summary


def record_generated_assets(
    cost_summary: CostSummary,
    generated_assets: list[GeneratedAsset],
    *,
    is_retry: bool,
) -> CostSummary:
    """Record generated assets and optional provider usage metadata."""

    cost_summary.total_generation_calls += len(generated_assets)
    if is_retry:
        cost_summary.total_retry_calls += len(generated_assets)

    fallback_image_generations = 0
    for asset in generated_assets:
        cost_summary.per_asset_calls[asset.spec_id] = (
            cost_summary.per_asset_calls.get(asset.spec_id, 0) + 1
        )
        usage_payload = asset.metadata.get("provider_usage")
        if usage_payload:
            record_provider_usage(cost_summary, ProviderUsage.model_validate(usage_payload))
        else:
            fallback_image_generations += 1

    cost_summary.total_image_generations += fallback_image_generations
    return cost_summary
