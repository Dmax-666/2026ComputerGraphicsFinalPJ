"""Pre-run API budget estimation."""

from graphic_agent.schemas import ProviderProfile, RunBudgetEstimate, ScenarioConfig


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
